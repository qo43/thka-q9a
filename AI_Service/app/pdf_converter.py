"""
PDF to JPG Converter Module

This module provides functionality to convert PDF files to JPG images.
Supports multi-page PDFs with configurable quality and resolution.
Uses PyMuPDF (fitz) for PDF processing and image rendering.
"""

import os
from pathlib import Path
from typing import List, Optional, Union

import fitz   # type: ignore


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
        pdf_path: Path to the input PDF file
        output_dir: Directory to save output JPG files. If None, uses the same directory as the PDF
        dpi: Resolution for the conversion (higher = better quality, larger file)
        quality: JPG quality (1-100, higher = better quality, larger file)
        output_prefix: Prefix for output filenames (e.g., "page" -> page_1.jpg, page_2.jpg)
        single_image: If True, merge all pages into a single tall image
    
    Returns:
        List of paths to the generated JPG file(s)
    
    Raises:
        FileNotFoundError: If the PDF file doesn't exist
        ValueError: If the PDF file is invalid or empty
    """
    pdf_path = Path(pdf_path)
    
    # Validate input file
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    if not pdf_path.is_file():
        raise ValueError(f"Path is not a file: {pdf_path}")
    
    if pdf_path.suffix.lower() != '.pdf':
        raise ValueError(f"File is not a PDF: {pdf_path}")
    
    # Set output directory
    if output_dir is None:
        output_dir = pdf_path.parent
    else:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Open PDF with PyMuPDF
    try:
        pdf_document = fitz.open(str(pdf_path))
    except Exception as e:
        raise ValueError(f"Failed to open PDF: {str(e)}")
    
    if pdf_document.page_count == 0:
        pdf_document.close()
        raise ValueError(f"PDF file appears to be empty: {pdf_path}")
    
    output_files = []
    zoom = dpi / 72  # Convert DPI to zoom factor (72 is PDF default)
    matrix = fitz.Matrix(zoom, zoom)
    
    try:
        if single_image and pdf_document.page_count > 1:
            # Merge all pages into a single tall image
            page_images = []
            max_width = 0
            total_height = 0
            
            # Render all pages first
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=matrix)
                page_images.append(pix)
                max_width = max(max_width, pix.width)
                total_height += pix.height
            
            # Create merged image using PyMuPDF
            merged_pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, max_width, total_height), False)
            merged_pix.set_rect(merged_pix.irect, (255, 255, 255))  # White background
            
            y_offset = 0
            for pix in page_images:
                # Center the image if narrower than the widest page
                x_offset = (max_width - pix.width) // 2
                merged_pix.copy(pix, fitz.IRect(x_offset, y_offset, x_offset + pix.width, y_offset + pix.height))
                y_offset += pix.height
            
            # Save merged image
            output_filename = f"{pdf_path.stem}_{output_prefix}_merged.jpg"
            output_path = output_dir / output_filename
            merged_pix.save(str(output_path), "jpeg", jpg_quality=quality)
            output_files.append(str(output_path))
            
        else:
            # Save each page as a separate JPG
            for page_num in range(pdf_document.page_count):
                page = pdf_document[page_num]
                pix = page.get_pixmap(matrix=matrix)
                
                if pdf_document.page_count == 1:
                    # Single page PDF - no page number in filename
                    output_filename = f"{pdf_path.stem}.jpg"
                else:
                    # Multi-page PDF - include page number
                    output_filename = f"{pdf_path.stem}_{output_prefix}_{page_num + 1}.jpg"
                
                output_path = output_dir / output_filename
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
    """
    Convert multiple PDF files to JPG images.
    
    Args:
        pdf_files: List of paths to PDF files
        output_dir: Directory to save all output JPG files
        dpi: Resolution for the conversion
        quality: JPG quality (1-100)
        single_image: If True, merge pages of each PDF into single images
    
    Returns:
        Dictionary mapping input PDF paths to lists of output JPG paths
        Failed conversions will have their error messages as values
    """
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
        except Exception as e:
            results[str(pdf_file)] = f"Error: {str(e)}"
    
    return results


def get_pdf_info(pdf_path: Union[str, Path]) -> dict:
    """
    Get information about a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
    
    Returns:
        Dictionary containing PDF information (page count, file size, etc.)
    """
    pdf_path = Path(pdf_path)
    
    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    try:
        pdf_document = fitz.open(str(pdf_path))
        page_count = pdf_document.page_count
        pdf_document.close()
    except Exception as e:
        raise ValueError(f"Failed to read PDF: {str(e)}")
    
    file_size_bytes = pdf_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    return {
        "filename": pdf_path.name,
        "path": str(pdf_path),
        "page_count": page_count,
        "file_size_bytes": file_size_bytes,
        "file_size_mb": round(file_size_mb, 2),
    }
