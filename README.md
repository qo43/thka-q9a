# Wathiq Prototype (OCR - Python Version)

## How to Run
1. Open the folder in **VS Code** or any code editor.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
3. Run the server:
    ```bash
    python -m uvicorn main:app --reload
4. The Backend runs on http://localhost:8000

## API Endpoints
- **POST** /api/scan
    - **Input:** Upload an image
    - **Output:** Returns JSON with text, validation status, year, and confidence score.

 
