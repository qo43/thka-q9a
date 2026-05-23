"""
PDF conversion helpers used by the OCR service.

The upload endpoint works mostly in memory, while a few utility functions still
support converting PDFs from disk for tests and manual workflows.
"""

import os
import logging
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import fitz  # type: ignore
import numpy as np


logger = logging.getLogger("wathiq")


def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract selectable text from an in-memory PDF."""
    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            return "\n".join(page.get_text("text") for page in doc).strip()
    except Exception:
        return ""


def convert_pdf_bytes_to_image(file_bytes: bytes) -> Tuple[Optional[np.ndarray], Optional[str]]:
    """
    Convert the first page of an in-memory PDF to an OpenCV BGR image.
    Returns (image, error_message).
    """
    if len(file_bytes) == 0:
        return None, "الملف فارغ."

    if not file_bytes.startswith(b"%PDF"):
        return None, "الملف ليس بتنسيق PDF صالح."

    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            if doc.page_count == 0:
                return None, "ملف PDF فارغ."

            page = doc[0]
            zoom = 150 / 72
            matrix = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=matrix, alpha=False)

            img_data = np.frombuffer(pix.samples, dtype=np.uint8)
            img_data = img_data.reshape(pix.h, pix.w, pix.n)

            if pix.n >= 3:
                img = cv2.cvtColor(img_data, cv2.COLOR_RGB2BGR)
            else:
                img = cv2.cvtColor(img_data, cv2.COLOR_GRAY2BGR)

            return img, None

    except Exception as exc:
        error_msg = str(exc)
        lower_error = error_msg.lower()

        if "cannot open broken document" in lower_error:
            return None, "ملف PDF تالف أو غير صالح."
        if "password" in lower_error:
            return None, "ملف PDF محمي بكلمة مرور."
        return None, f"حدث خطأ أثناء معالجة ملف PDF: {error_msg}"


def convert_pdf_to_jpg(
    pdf_path: Union[str, Path],
    output_dir: Optional[Union[str, Path]] = None,
    dpi: int = 200,
    quality: int = 85,
    output_prefix: str = "page",
    single_image: bool = False,
) -> List[str]:
    """
    Convert a PDF file to JPG image(s).

    Args:
        pdf_path: Path to the input PDF file.
        output_dir: Directory to save output JPG files. If omitted, uses the PDF directory.
        dpi: Render resolution.
        quality: JPG quality from 1 to 100.
        output_prefix: Prefix for multi-page output filenames.
        single_image: Merge all pages into one tall image when True.
    """
    pdf_path = Path(pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")

    if pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")

    if output_dir is None:
        output_dir = pdf_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

    try:
        pdf_document = fitz.open(str(pdf_path))
    except Exception as exc:
        raise ValueError(f"Failed to open PDF: {exc}") from exc

    if pdf_document.page_count == 0:
        pdf_document.close()
        raise ValueError(f"PDF file appears to be empty: {pdf_path}")

    output_files = []
    zoom = dpi / 72
    matrix = fitz.Matrix(zoom, zoom)

    try:
        if single_image and pdf_document.page_count > 1:
            page_images = []
            max_width = 0
            total_height = 0

            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                page_images.append(pix)
                max_width = max(max_width, pix.width)
                total_height += pix.height

            merged_pix = fitz.Pixmap(
                fitz.csRGB,
                fitz.IRect(0, 0, max_width, total_height),
                False,
            )
            merged_pix.set_rect(merged_pix.irect, (255, 255, 255))

            y_offset = 0
            for pix in page_images:
                x_offset = (max_width - pix.width) // 2
                merged_pix.copy(
                    pix,
                    fitz.IRect(x_offset, y_offset, x_offset + pix.width, y_offset + pix.height),
                )
                y_offset += pix.height

            output_filename = f"{pdf_path.stem}_{output_prefix}_merged.jpg"
            output_path = Path(output_dir) / output_filename
            merged_pix.save(str(output_path), "jpeg", jpg_quality=quality)
            output_files.append(str(output_path))

        else:
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=matrix, alpha=False)

                if pdf_document.page_count == 1:
                    output_filename = f"{pdf_path.stem}.jpg"
                else:
                    output_filename = f"{pdf_path.stem}_{output_prefix}_{page_num + 1}.jpg"

                output_path = Path(output_dir) / output_filename
                pix.save(str(output_path), "jpeg", jpg_quality=quality)
                output_files.append(str(output_path))

    finally:
        pdf_document.close()

    return output_files


def convert_pdf_batch(
    pdf_files: List[Union[str, Path]],
    output_dir: Optional[Union[str, Path]] = None,
    dpi: int = 200,
    quality: int = 85,
    single_image: bool = False,
) -> dict:
    """Convert multiple PDF files to JPG images."""
    results = {}

    for pdf_file in pdf_files:
        try:
            output_files = convert_pdf_to_jpg(
                pdf_path=pdf_file,
                output_dir=output_dir,
                dpi=dpi,
                quality=quality,
                single_image=single_image,
            )
            results[str(pdf_file)] = output_files
        except Exception as exc:
            results[str(pdf_file)] = f"Error: {exc}"

    return results


def get_pdf_info(pdf_path: Union[str, Path, bytes]) -> dict:
    """
    Get basic information about a PDF path or in-memory PDF bytes.
    """
    pdf_document = None
    file_size_bytes = 0
    filename = "unknown"
    path_str = "memory"

    try:
        if isinstance(pdf_path, (bytes, bytearray)):
            pdf_document = fitz.open(stream=pdf_path, filetype="pdf")
            file_size_bytes = len(pdf_path)
            filename = "uploaded_file.pdf"
        else:
            pdf_path = Path(pdf_path)
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF file not found: {pdf_path}")

            pdf_document = fitz.open(str(pdf_path))
            file_size_bytes = pdf_path.stat().st_size
            filename = pdf_path.name
            path_str = str(pdf_path)

        info = {
            "filename": filename,
            "path": path_str,
            "page_count": pdf_document.page_count,
            "file_size_bytes": file_size_bytes,
            "file_size_mb": round(file_size_bytes / (1024 * 1024), 2),
            "is_encrypted": pdf_document.is_encrypted,
        }
        pdf_document.close()
        return info

    except Exception as exc:
        if pdf_document is not None:
            pdf_document.close()
        raise ValueError(f"Failed to read PDF: {exc}") from exc


def create_thumbnail(pdf_path: Union[str, Path], output_folder: Union[str, Path]) -> Optional[str]:
    """Create a low-resolution thumbnail of the first PDF page."""
    try:
        with fitz.open(str(pdf_path)) as doc:
            page = doc[0]
            pix = page.get_pixmap(matrix=fitz.Matrix(0.5, 0.5), alpha=False)

            thumb_name = os.path.basename(str(pdf_path)).replace(".pdf", "_thumb.jpg")
            thumb_path = Path(output_folder) / thumb_name
            pix.save(str(thumb_path))

            return str(thumb_path)
    except Exception as exc:
        logger.exception("document.thumbnail_failed path=%s error=%s", pdf_path, exc)
        return None
