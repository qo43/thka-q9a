from pathlib import Path
import logging
import re
import time
import uuid
from logging.handlers import RotatingFileHandler

import cv2
import easyocr
import numpy as np
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from AI_Service.app import classifier, explaination_generation, pdf_converter


BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "accepted_documents"
UPLOAD_DIR.mkdir(exist_ok=True)
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / "wathiq.log"

# AI model setting.
# Developers can change this value to any installed Ollama model.
OLLAMA_MODEL = "qwen2.5:7b-instruct"

logger = logging.getLogger("wathiq")
logger.setLevel(logging.INFO)
logger.propagate = False

if not logger.handlers:
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=1_000_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    logger.addHandler(file_handler)

app = FastAPI(
    title="Wathiq OCR API",
    description="Intelligent OCR API for reviewing Saudi legal documents.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount(
    "/Web_Interface",
    StaticFiles(directory=BASE_DIR / "Web_Interface", html=True),
    name="web_interface",
)

logger.info("startup.easyocr.loading")
reader = easyocr.Reader(["ar", "en"], gpu=False)
logger.info("startup.easyocr.loaded")

ARABIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
SUPPORTED_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png")
MIN_DIRECT_TEXT_LENGTH = 20


@app.get("/")
async def home():
    return RedirectResponse(url="/Web_Interface/")


@app.get("/api/config")
async def get_config():
    return {
        "model": OLLAMA_MODEL,
        "logFile": str(LOG_FILE),
    }


def mask_national_id(national_id: str | None) -> str:
    national_id = (national_id or "").strip()
    if len(national_id) < 4:
        return ""
    return f"******{national_id[-4:]}"


def normalize_arabic_numbers(text: str) -> str:
    """Convert Arabic and Persian digits to Western digits for parsing."""
    return text.translate(ARABIC_DIGITS)


def save_for_database(file_bytes: bytes, original_filename: str | None) -> str | None:
    try:
        timestamp = int(time.time())
        clean_name = Path(original_filename or "document").name
        clean_name = re.sub(r"[^\w.\-\u0600-\u06FF ]+", "_", clean_name).strip(" ._")
        clean_name = clean_name or "document"

        save_path = UPLOAD_DIR / f"{timestamp}_{clean_name}"
        with save_path.open("wb") as file:
            file.write(file_bytes)

        logger.info("document.saved path=%s", save_path)
        return str(save_path)
    except Exception as exc:
        logger.exception("document.save_failed error=%s", exc)
        return None


def is_supported_image(file_bytes: bytes, filename: str) -> bool:
    has_image_extension = filename.endswith(SUPPORTED_IMAGE_EXTENSIONS)
    has_jpg_header = file_bytes.startswith(b"\xff\xd8")
    has_png_header = file_bytes.startswith(b"\x89PNG")
    return has_image_extension and (has_jpg_header or has_png_header)


def decode_image(file_bytes: bytes) -> np.ndarray | None:
    image_buffer = np.frombuffer(file_bytes, np.uint8)
    return cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)


def detect_language(text: str) -> str:
    arabic_count = sum("\u0600" <= char <= "\u06FF" for char in text)
    english_count = sum(char.isascii() and char.isalpha() for char in text)
    return "ar" if arabic_count >= english_count else "en"


def clean_extracted_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"\bfile:///\S+", "", text)
    text = re.sub(r"\b\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}\s*(?:AM|PM)?", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d+/\d+\b$", "", text).strip()
    return re.sub(r"\s+", " ", text).strip()


def split_segments(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []

    parts = re.split(r"(?<=[.!؟،؛])\s+|\n+", text)
    return [part.strip() for part in parts if part.strip()]


def find_segment(text: str, pattern: str, lang: str = "ar") -> str:
    for index, segment in enumerate(split_segments(text), start=1):
        if re.search(pattern, segment, flags=re.IGNORECASE):
            excerpt = segment[:160] + ("..." if len(segment) > 160 else "")
            label = "الموضع" if lang == "ar" else "Location"
            return f"{label} {index}: {excerpt}"
    return "المستند بالكامل" if lang == "ar" else "Whole document"


def add_issue(
    issues: list[dict],
    severity: str,
    where: str,
    problem: str,
    suggestion: str,
    replacement: str,
) -> None:
    issues.append(
        {
            "severity": severity,
            "where": where,
            "problem": problem,
            "suggestion": suggestion,
            "replacement": replacement,
        }
    )


def build_heuristic_review(text: str, lang: str) -> list[dict]:
    normalized = normalize_arabic_numbers(text)
    lowered = normalized.lower()
    issues: list[dict] = []

    if re.search(r"\?{3,}|_{3,}|\|{3,}|�", text):
        add_issue(
            issues,
            "high",
            find_segment(text, r"\?{3,}|_{3,}|\|{3,}|�", lang),
            "يوجد نص غير مفهوم أو أثر من أخطاء OCR.",
            "راجع هذا الموضع وأعد كتابته من المصدر الأصلي قبل الاعتماد عليه.",
            "استبدل النص غير المفهوم بعبارة واضحة ومثبتة من المستند الأصلي.",
        )

    if not re.search(r"(?<!\d)(14|20)\d{2}(?!\d)", normalized):
        add_issue(
            issues,
            "medium",
            "بيانات المستند",
            "لا يظهر تاريخ واضح في النص.",
            "أضف التاريخ الهجري أو الميلادي المرتبط بالواقعة أو الطلب.",
            "بتاريخ .../ .../ 1447هـ وقعت الواقعة محل الطلب.",
        )

    if lang == "ar":
        if not re.search(r"المحكمة|ديوان المظالم|فضيلة|رئيس", text):
            add_issue(
                issues,
                "medium",
                "بداية المستند",
                "لا توجد جهة قضائية أو افتتاحية رسمية واضحة.",
                "ابدأ الخطاب بتوجيهه إلى المحكمة أو الجهة المختصة.",
                "إلى فضيلة رئيس المحكمة المختصة حفظه الله",
            )

        if not re.search(r"المدعي|مقدم الطلب|مقدم الشكوى|المدعى عليه|المشكو ضده", text):
            add_issue(
                issues,
                "high",
                "بيانات الأطراف",
                "الأطراف غير محددين بوضوح.",
                "اذكر مقدم الطلب والخصم بصفاتهم النظامية قبل عرض الوقائع.",
                "مقدم الطلب: ...\nضد: ...",
            )

        if not re.search(r"الوقائع|تتلخص|حيث|تتمثل", text):
            add_issue(
                issues,
                "medium",
                "عرض الوقائع",
                "الوقائع غير منظمة تحت عنوان واضح.",
                "اجعل الوقائع في نقاط مرتبة زمنياً.",
                "الوقائع:\n1. ...\n2. ...",
            )

        if not re.search(r"الطلبات|أطلب|نلتمس|يلتمس|الحكم", text):
            add_issue(
                issues,
                "high",
                "خاتمة المستند",
                "لا توجد طلبات قضائية محددة.",
                "اختم المستند بطلبات واضحة قابلة للنظر.",
                "الطلبات:\n1. الحكم بـ ...\n2. إلزام المدعى عليه بـ ...",
            )

        if re.search(r"\b(انا|ابي|ابغى|اريد|فلوسي|ما عطاني|ما اعطاني)\b", lowered):
            add_issue(
                issues,
                "medium",
                find_segment(lowered, r"\b(انا|ابي|ابغى|اريد|فلوسي|ما عطاني|ما اعطاني)\b", lang),
                "توجد عبارات عامية أو شخصية لا تناسب الصياغة القضائية.",
                "حوّلها إلى صياغة رسمية ومحايدة.",
                "يتقدم مقدم الطلب بهذه الدعوى طالباً إلزام المدعى عليه بـ ...",
            )

    else:
        if not re.search(r"court|honorable|judge|tribunal", lowered):
            add_issue(
                issues,
                "medium",
                "Document opening",
                "The court or addressee is not clearly stated.",
                "Open the document with the competent court or authority.",
                "To the Honorable President of the Competent Court",
            )

        if not re.search(r"plaintiff|claimant|complainant|defendant|respondent", lowered):
            add_issue(
                issues,
                "high",
                "Party details",
                "The parties are not clearly identified.",
                "State the claimant and respondent before the facts.",
                "Claimant: ...\nRespondent: ...",
            )

        if not re.search(r"facts|whereas|background", lowered):
            add_issue(
                issues,
                "medium",
                "Facts section",
                "The facts are not organized under a clear section.",
                "List the facts chronologically.",
                "Facts:\n1. ...\n2. ...",
            )

        if not re.search(r"requests|relief|claimant requests|therefore", lowered):
            add_issue(
                issues,
                "high",
                "Requests section",
                "The requested relief is not clearly stated.",
                "End with specific judicial requests.",
                "Requests:\n1. Order the respondent to ...\n2. Award ...",
            )

        if re.search(r"\b(i want|i need|give me|my money|they didn't|they dont)\b", lowered):
            add_issue(
                issues,
                "medium",
                find_segment(lowered, r"\b(i want|i need|give me|my money|they didn't|they dont)\b", lang),
                "The wording is informal for a legal filing.",
                "Use formal and neutral legal phrasing.",
                "The claimant respectfully requests that the court order the respondent to ...",
            )

    long_segments = [segment for segment in split_segments(text) if len(segment) > 420]
    if long_segments:
        add_issue(
            issues,
            "low",
            long_segments[0][:160] + "...",
            "توجد فقرة طويلة قد تصعب قراءتها.",
            "قسّم الفقرة إلى وقائع وطلبات مرقمة.",
            "الوقائع:\n1. ...\n2. ...\n\nالطلبات:\n1. ...",
        )

    if not issues:
        add_issue(
            issues,
            "low",
            "المستند بالكامل",
            "لم تظهر أخطاء شكلية كبيرة في الفحص الآلي.",
            "يمكن تحسين الصياغة بزيادة التنظيم والعناوين القانونية عند الحاجة.",
            "استخدم عناوين واضحة: الأطراف، الوقائع، الطلبات.",
        )

    return issues[:8]


def build_fallback_rewrite(text: str, lang: str) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    excerpt = normalized[:900]

    if lang == "ar":
        name_match = re.search(
            r"(?:انا اسمي|اسمي)\s+(.+?)(?:\s+و(?:اريد|أريد|ابي|أبي|ابغى)|\s+على|\s+ضد|\.|،|$)",
            normalized,
        )
        respondent_match = re.search(
            r"(?:على|ضد)\s+(شركة\s+.+?)(?:\s+(?:لان|لأن|لانهم|لأنهم|النهم|ما|بسبب)|\.|،|$)",
            normalized,
        )
        amount_match = re.search(r"(\d[\d,]*)\s*(?:ريال|ر\.?س)|(?:ريال|لاير)\s*(\d[\d,]*)", normalize_arabic_numbers(normalized))

        claimant = name_match.group(1).strip() if name_match else "..."
        respondent = respondent_match.group(1).strip() if respondent_match else "..."
        amount = next((group for group in (amount_match.groups() if amount_match else []) if group), None)
        amount_text = f" بمبلغ ({amount}) ريال سعودي" if amount else ""

        return (
            "إلى فضيلة رئيس المحكمة المختصة حفظه الله\n"
            "السلام عليكم ورحمة الله وبركاته\n\n"
            f"مقدم الطلب: {claimant}\n"
            f"المدعى عليه: {respondent}\n\n"
            "الموضوع: مطالبة مالية\n\n"
            "الوقائع:\n"
            f"1. يذكر مقدم الطلب أن له مطالبة مالية على المدعى عليه{amount_text}.\n"
            "2. يذكر مقدم الطلب أنه طالب المدعى عليه بالسداد أكثر من مرة دون نتيجة.\n"
            f"3. ورد في المستند النص الآتي بعد استخراجه: {excerpt}\n\n"
            "الطلبات:\n"
            "1. قبول الدعوى شكلاً.\n"
            "2. إلزام المدعى عليه بسداد المبلغ المستحق متى ثبت ذلك للمحكمة.\n"
            "3. الحكم بما تراه المحكمة محققاً للعدل وفق الأنظمة المرعية.\n\n"
            "والله ولي التوفيق."
        )

    return (
        "To the Honorable President of the Competent Court\n"
        "Peace and blessings be upon you\n\n"
        "Subject: Legal Claim for Judicial Review\n\n"
        "The claimant respectfully submits this claim based on the facts contained "
        "in the attached document, after organizing the wording and removing informal "
        "or unclear expressions.\n\n"
        "Facts:\n"
        f"1. {excerpt}\n\n"
        "Requests:\n"
        "1. Accept the claim procedurally.\n"
        "2. Review the merits of the claim and issue the appropriate judgment.\n"
        "3. Order the respondent to comply with any obligations established by the court.\n\n"
        "With highest respect and appreciation."
    )


def build_review(text: str, lang: str, model_name: str = OLLAMA_MODEL) -> dict:
    issues = build_heuristic_review(text, lang)

    try:
        classification = classifier.classify_with_ollama(
            text,
            lang=lang,
            model=model_name,
            timeout_s=12,
        )
    except Exception as exc:
        logger.exception("ai.classification_failed model=%s lang=%s error=%s", model_name, lang, exc)
        classification = {
            "case_type": "Other",
            "urgency": "Normal",
            "handling_unit": "InitialIntake",
            "confidence": 0.0,
            "reason": f"Classification failed: {exc}",
            "highlights": [],
        }

    explanation = {"success": False, "reason": "Rule-based rewrite used."}
    try:
        explanation = explaination_generation.generate_explanation(
            text,
            lang=lang,
            model=model_name,
            timeout_s=30,
        )
    except Exception as exc:
        logger.exception("ai.rewrite_failed model=%s lang=%s error=%s", model_name, lang, exc)
        explanation = {"success": False, "reason": f"Generation failed: {exc}"}

    best_rewrite = explanation.get("message") if explanation.get("success") else build_fallback_rewrite(text, lang)

    return {
        "language": lang,
        "classification": classification,
        "issues": issues,
        "bestRewrite": best_rewrite,
        "rewriteSource": "ollama" if explanation.get("success") else "rule-based",
        "generationReason": explanation.get("reason", ""),
        "model": model_name,
        "summary": (
            "تم استخراج النص وتحليل الصياغة واقتراح نسخة قانونية محسنة."
            if lang == "ar"
            else "The document was extracted, reviewed, and rewritten in a stronger legal style."
        ),
    }


def analyze_extracted_text(extracted_text: str, avg_confidence: float):
    normalized_text = normalize_arabic_numbers(extracted_text)
    readable_units = len(normalized_text.split())

    year_match = re.search(r"(?<!\d)14[0-9]{2}(?!\d)", normalized_text)
    detected_year = year_match.group(0) if year_match else "غير معروف"

    if readable_units < 3 or avg_confidence < 0.4:
        return False, detected_year, "الصورة غير واضحة. واجه النظام صعوبة في قراءة النصوص."

    return True, detected_year, f"تم تحليل المستند بنجاح. مستند لعام {detected_year}."


@app.post("/api/scan")
async def scan_document(
    name: str = Form(""),
    national_id: str = Form(""),
    file: UploadFile = File(...),
):
    """
    Extract, review, and rewrite one uploaded legal document.
    Supports PDF, JPG, JPEG, and PNG.
    """
    request_id = str(uuid.uuid4())
    selected_model = OLLAMA_MODEL
    file_bytes = await file.read()
    original_filename = file.filename or "document"
    filename = original_filename.lower()
    img = None
    direct_pdf_text = ""

    def reject(reason: str) -> dict:
        logger.warning(
            "scan.reject request_id=%s file=%s model=%s reason=%s",
            request_id,
            original_filename,
            selected_model,
            reason,
        )
        return {
            "text": "",
            "isValid": False,
            "reason": reason,
            "requestId": request_id,
            "model": selected_model,
        }

    try:
        logger.info(
            "scan.start request_id=%s file=%s size_bytes=%s model=%s name_present=%s national_id=%s",
            request_id,
            original_filename,
            len(file_bytes),
            selected_model,
            bool(name.strip()),
            mask_national_id(national_id),
        )

        if len(file_bytes) == 0:
            return reject("الملف المرفق فارغ.")

        if filename.endswith(".pdf"):
            try:
                file_info = pdf_converter.get_pdf_info(file_bytes)
            except ValueError:
                return reject("ملف PDF غير صالح أو تالف.")

            if file_info["page_count"] > 10:
                return reject("الملف يحتوي على أكثر من 10 صفحات. يرجى رفع ملف أصغر.")

            if file_info["is_encrypted"]:
                return reject("الملف محمي بكلمة مرور ولا يمكن معالجته.")

            extracted_pdf_text = pdf_converter.extract_pdf_text(file_bytes)

            if len(extracted_pdf_text.split()) >= MIN_DIRECT_TEXT_LENGTH:
                direct_pdf_text = extracted_pdf_text
            else:
                img, error = pdf_converter.convert_pdf_bytes_to_image(file_bytes)
                if img is None:
                    return reject(error or "تعذر قراءة ملف PDF.")

        elif is_supported_image(file_bytes, filename):
            img = decode_image(file_bytes)
            if img is None:
                return reject("تعذر قراءة الصورة. تأكد من أن الملف غير تالف.")

        else:
            return reject("صيغة الملف غير مدعومة. الصيغ المدعومة: PDF و JPG و PNG.")

        if direct_pdf_text:
            extracted_text = clean_extracted_text(direct_pdf_text)
            avg_confidence = 1.0
            logger.info("ocr.direct_pdf_text request_id=%s", request_id)
        else:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            raw_results = reader.readtext(
                img,
                detail=1,
                paragraph=False,
                mag_ratio=1,
                link_threshold=0.1,
            )

            total_confidence = 0
            extracted_text_list = []

            for _bbox, text, prob in raw_results:
                extracted_text_list.append(text)
                total_confidence += prob

            word_count = len(extracted_text_list)
            avg_confidence = (total_confidence / word_count) if word_count > 0 else 0
            logger.info("ocr.easyocr request_id=%s confidence=%.2f words=%s", request_id, avg_confidence, word_count)

            extracted_text = clean_extracted_text(" ".join(extracted_text_list))

        saved_path = None
        is_valid, detected_year, reason = analyze_extracted_text(extracted_text, avg_confidence)
        lang = detect_language(extracted_text)
        review = build_review(extracted_text, lang, selected_model) if is_valid else None

        if is_valid:
            saved_path = save_for_database(file_bytes, original_filename)

            if saved_path and filename.endswith(".pdf"):
                thumb_path = pdf_converter.create_thumbnail(saved_path, UPLOAD_DIR)
                logger.info("document.thumbnail request_id=%s path=%s", request_id, thumb_path)

        logger.info(
            "scan.finish request_id=%s valid=%s lang=%s year=%s confidence=%.2f issues=%s rewrite_source=%s model=%s",
            request_id,
            is_valid,
            lang,
            detected_year,
            avg_confidence,
            len(review.get("issues", [])) if review else 0,
            review.get("rewriteSource") if review else "none",
            selected_model,
        )

        return {
            "text": extracted_text,
            "isValid": is_valid,
            "caseYear": detected_year,
            "reason": reason,
            "debugScore": avg_confidence,
            "databasePath": saved_path,
            "review": review,
            "requestId": request_id,
            "model": selected_model,
        }

    except Exception as exc:
        logger.exception("scan.error request_id=%s model=%s error=%s", request_id, selected_model, exc)
        return {
            "text": "",
            "isValid": False,
            "reason": "حدث خطأ داخلي.",
            "requestId": request_id,
            "model": selected_model,
        }
