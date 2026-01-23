
import os
import time
import re
import cv2
import easyocr
import fitz
import torch
import numpy as np
from pathlib import Path
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .AI_Service.app import pdf_converter
from .AI_Service.app import explanation_generation
from .schemas import DraftRequest, DraftResponse, ScanResponse

torch.set_num_threads(4)  # Limit PyTorch to use only 4 CPU threads to prevent bottelenecks
# --- FASTAPI SETUP ---
app = FastAPI(
    title="Wathiq OCR API",
    description="Intelligent OCR API for validating Saudi Legal Documents.",
    version="1.0.0"
)

# --- UPLOAD DIRECTORY SETUP ---
UPLOAD_DIR = "accepted_documents"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Enables CORS for Frontend Communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# Mount the website to allow calling the API
# BASE_DIR, because you need to use an absolute path when mounting
BASE_DIR = Path(__file__).resolve().parent
app.mount(
    "/Web_Interface/",
    StaticFiles(directory= BASE_DIR / "Web_Interface", html=True)
)

# --- LOAD EASYOCR MODEL ---
# We load the model once when the server starts to ensure fast responses.
# GPU is set to False for compatibility. Set to True if a GPU is available.
print("Loading EasyOCR...")
reader = easyocr.Reader(['ar'], gpu=False) 
print("EasyOCR Loaded!")

# --- ARABIC NUMBER NORMALIZER ---
def normalize_arabic_numbers(text):
    """
    Converts Arabic numerals (١٢٣) to Standard Arabic numerals (123).
    Required for year parsing and storage.
    """
    translation_table = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    return text.translate(translation_table)

def save_document(file_bytes, original_filename):
    """
    Saves the approved file to the UPLOAD_DIR with a unique name (timestamp + original name).
    Returns the path where the file is saved.
    """
    try:
        # Example: 1701301234_originalfilename.pdf
        timestamp = int(time.time())
        clean_name = os.path.basename(original_filename)
        unique_name = f"{timestamp}_{clean_name}"
        save_path = os.path.join(UPLOAD_DIR, unique_name)
        with open(save_path, "wb") as f:
            f.write(file_bytes)

        print(f"Saved approved document to: {save_path}")
        return save_path
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

# --- AI GENERATION ENDPOINT ---
@app.post("/api/draft")
async def draft_explanation(request: DraftRequest) -> DraftResponse:
    """
    Endpoint to provide explanation for draft documents.
    Frontend should call this after /api/scan returns success.
    """
    # A safe text limit to avoid crashing the AI with huge inputs
    safe_text = request.ocr_text[:2000]

    try:
        result = explanation_generation.generate_explanation(safe_text)
    except Exception as e:
        print(f"AI Generator Crashed: {e}")
        return {"draft": "حدث خطأ أثناء توليد الشرح.", "status": "error", "reason": "System Error"}
    
    response_payload = {
        "draft": result.get("message", ""),
        "status": "success" if result.get("success") else "error",
        "reason": result.get("reason", "")
    }
    
    return response_payload

@app.post("/api/scan")
async def scan_document(file: UploadFile = File(...)) -> ScanResponse:
    """
    Main Pipeline for document scanning and validation.
    1. In-Memroy Image Handling (No file I/O on server)
    2. OCR with Arabic tuning
    3. Confidence Calculation
    4. Context Validation
    5. Year Extraction
    """

    # 0. READ IMAGE INTO MEMORY
    # Using in-memroy bytes to avoid file I/O
    file_bytes = await file.read()
    filename = file.filename.lower()
    img = None
    file_Info = None

    try:
        # 1. CHECK FOR EMPTY FILE
        if len(file_bytes) == 0:
            return {"isValid": False, "reason": "الملف المرفق فارغ."}

        # 2. PDF/IMAGE DECODING
        # Converts raw bytes to OpenCV image object and handles PDF conversion if needed
        # First check if the file is a PDF
        if filename.endswith('.pdf'):
            # Try reading PDF directly with fitz (PyMuPDF) for text extraction
            try:
                print("Reading PDF with fitz...")
                with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                    text_content = ""
                    for page in doc:
                        text_content += page.get_text()
                    print("PDF text extraction with fitz completed.")

                    if len(text_content) > 50:
                        detected_year = "Unknown"
                        year_match = re.search(r'(?:14|١٤)[0-9٠-٩]{2}', text_content)
                        if year_match:
                            detected_year = normalize_arabic_numbers(year_match.group(0))
                        return {
                            "extractedText": text_content,
                            "isValid": True, 
                            "caseYear": detected_year,
                            "reason": "تم استخراج النص مباشرة.",
                            "debugScore": 1.0
                        }
            except Exception as e:
                print(f"Error reading PDF with fitz will fall back to OCR: {e}")

            # If fitz extraction fails fall back to image conversion
            # Fetch PDF file info using pdf_processor module
            print("Getting PDF info...")
            file_Info = pdf_converter.get_pdf_info(file_bytes)
            print(f"PDF Info: {file_Info}")

            if file_Info is None:
                return {"isValid": False, "reason": "ملف PDF تالف أو غير صالح."}

            # If the PDF has more than 10 pages then reject it
            if file_Info and file_Info['page_count'] > 10:
                return {"isValid": False, "reason": "الملف يحتوي على أكثر من 10 صفحات. يرجى رفع ملف أصغر."}
            
            if file_Info and file_Info['is_encrypted']:
                return {"isValid": False, "reason": "الملف محمي بكلمة مرور ولا يمكن معالجته."}

            # Convert PDF bytes to image using pdf_processor function
            print("Converting PDF to image for OCR...")
            img, error = pdf_converter.convert_pdf_bytes_to_image(file_bytes)
            print("PDF to image conversion completed.")
            if img is None:
                return {"isValid": False, "reason": error}
        else:
            # Assume it's an image file (JPG/PNG) and decode directly
            # Check the image header to ensure it is a valid image
            # JPG header: FF D8. PNG header: 89 50.
            header = file_bytes[:4].hex().upper()
            is_valid_image = header.startswith('FFD8') or header.startswith('8950')
            
            nparr = np.frombuffer(file_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if img is None:
                if not is_valid_image:
                    return {"isValid": False, "reason": "الملف لا يبدو كصورة صالحة هل قمت بتغيير امتداد الملف؟ الملفات المدعومة: الصور وملفات PDF."}
                else:
                    return {"isValid": False, "reason": "تعذر قراءة الصورة. تأكد من أن الملف غير تالف."}
            
        # 2.5 PROCESSING ENHANCEMENTS
        height, width = img.shape[:2]

        # Resize large images for faster processing
        MAX_WIDTH = 1280
        if width > MAX_WIDTH:
            scaling_factor = MAX_WIDTH / float(width)
            new_height = int(height * scaling_factor)
            img = cv2.resize(img, (MAX_WIDTH, new_height), interpolation=cv2.INTER_AREA)

        # Convert to grayscale
        print("Converting image to grayscale...")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        print("Image converted to grayscale.")

        # 3. OCR PROCESSING
        # detail=1: returns returns bounding box, text, and confidence score
        # We need confidence scores for validation
        # Note: paragraph=False to get word-level scores instead of paragraph-level
        # mag_ratio=1: for better accuracy on small text it increases image size before processing
        # link_threshold=0.1: to help with connected text in Arabic documents
        print("Starting OCR processing with EasyOCR...")
        start_ocr = time.time()
        raw_results = reader.readtext(
            img, 
            detail=1,
            paragraph=False,
            mag_ratio=1,
            link_threshold=0.1,
            decoder='greedy',
            beamWidth=1
        )
        end_ocr = time.time()
        print(f"OCR processing completed in {end_ocr - start_ocr:.2f} seconds.")
        
        # 4. CALCULATE CONFIDENCE
        total_confidence = 0
        word_count = 0
        extracted_text_list = []

        print("Starting OCR result processing...")
        for (bbox, text, prob) in raw_results:
            extracted_text_list.append(text)
            total_confidence += prob
            word_count += 1
        print("OCR result processing completed.")

        # Determine average confidence score
        avg_confidence = (total_confidence / word_count) if word_count > 0 else 0
        
        print(f"Average OCR Confidence: {avg_confidence:.2f}") # For example 0.85

        # Reassemble full extracted text
        extracted_text = " ".join(extracted_text_list)

        # 5. CONTEXT VALIDATION
        # Check for presence of key legal terms in the extracted text to validate document type
        keywords = [
            "ديوان المظالم", "المحكمة الإدارية", "صحيفة دعوى", 
            "رقم القضية", "صك حكم", "بسم الله", "المملكة العربية"
        ]
        is_valid = any(word in extracted_text for word in keywords)

        # 6. YEAR EXTRACTION
        # Matches patterns like 1447 or ١٤٤٧
        year_match = re.search(r'(?:14|١٤)[0-9٠-٩]{2}', extracted_text)
        detected_year = "Unknown"
        if year_match:
            raw_year = year_match.group(0)
            detected_year = normalize_arabic_numbers(raw_year)
        # Add unknown year handling if needed

        # 7. FINAL DECISION LOGIC
        reason = ""
        saved_path = None
        
        # Gate 1: Confidence Check
        # If the AI confidence is too low, we reject the document
        if word_count < 3 or avg_confidence < 0.4:
            is_valid = False
            reason = "الصورة غير واضحة. الذكاء الاصطناعي وجد صعوبة في قراءة النصوص."
            # (Translation: Image unclear. AI struggled to read text.)
        
        # Gate 2: Context Check
        elif not is_valid:
            reason = "المستند لا يبدو تابعاً لديوان المظالم."
        
        # Gate 3: Success
        else:
            reason = f"تم التحقق بنجاح. مستند لعام {detected_year}."
            # Save approved document only if valid
            saved_path = save_document(file_bytes, filename)

            # We use this logic to create a preview image thumbnail for frontend display
            if saved_path and filename.endswith('.pdf'):
                thumb_path = pdf_converter.create_thumbnail(saved_path, UPLOAD_DIR)
                print(f"Thumbnail created at: {thumb_path}")
                    
        return {
            "extractedText": extracted_text,
            "isValid": is_valid,
            "caseYear": detected_year,
            "reason": reason,
            "debugScore": avg_confidence,
            "savePath": saved_path
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"extractedText": "", "isValid": False, "reason": "خطأ داخلي."}