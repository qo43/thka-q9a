from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import cv2
import numpy as np
import easyocr
import re

# --- FASTAPI SETUP ---
app = FastAPI(
    title="Wathiq OCR API",
    description="Intelligent OCR API for validating Saudi Legal Documents.",
    version="1.0.0"
)

# Enables CORS for Frontend Communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
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

@app.post("/api/scan")
async def scan_document(file: UploadFile = File(...)):
    """
    Main Pipeline for document scanning and validation.
    1. In-Memroy Image Handling (No file I/O on server)
    2. OCR with Arabic tuning
    3. Confidence Calculation
    4. Context Validation
    5. Year Extraction
    """

    #1. READ IMAGE INTO MEMORY
    # Using in-memroy bytes to avoid file I/O
    img_bytes = await file.read()

    try:
        # 2. IMAGE DECODING
        # Converts raw bytes to OpenCV image object
        nparr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # 3. OCR PROCESSING
        # detail=1: returns returns bounding box, text, and confidence score
        # We need confidence scores for validation
        # Note: paragraph=False to get word-level scores instead of paragraph-level
        # mag_ratio=2: for better accuracy on small text it increases image size before processing
        # link_threshold=0.1: to help with connected text in Arabic documents
        raw_results = reader.readtext(
            img, 
            detail=1,
            paragraph=False,
            mag_ratio=2,
            link_threshold=0.1
        )
        
        # 4. CALCULATE CONFIDENCE
        total_confidence = 0
        word_count = 0
        extracted_text_list = []

        for (bbox, text, prob) in raw_results:
            extracted_text_list.append(text)
            total_confidence += prob
            word_count += 1
        
        # Determine average confidence score
        avg_confidence = (total_confidence / word_count) if word_count > 0 else 0
        
        print(f"DEBUG: Average AI Confidence: {avg_confidence:.2f}") # e.g., 0.85

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

        # 7. FINAL DECISION LOGIC
        reason = ""
        
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

        return {
            "text": extracted_text,
            "isValid": is_valid,
            "caseYear": detected_year,
            "reason": reason,
            "debugScore": avg_confidence
        }

    except Exception as e:
        print(f"Error: {e}")
        return {"text": "", "isValid": False, "reason": "خطأ داخلي."}