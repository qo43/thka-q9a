from pydantic import BaseModel

class DraftRequest(BaseModel):
    """.
    Validates that the frontend sends a valid JSON object containing 'ocr_text'.
    This prevents the server from crashing if bad data is sent.
    """
    ocr_text: str

class DraftResponse(BaseModel):
    draft_text: str

class ScanResponse(BaseModel):
    extractedText: str
    isValid: bool
    caseYear: str
    reason: str
    debugScore: float
    savePath: str