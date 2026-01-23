# Wathiq Prototype

## How to Run
1. Open the folder in **VS Code** or any code editor.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
3. Run the server:
    - By terminal:
        ```bash
        python main.py
    - By simply hitting run button in the code editor
4. The Back-end runs on http://localhost:8000
5. The Front-end runs on http://localhost:8000/Web_Interface/index.html

## API Endpoints
- **POST** /api/scan
    - **Input:** Upload an image or a pdf document
    - **Output:** Returns JSON with text, validation status, year, and confidence score.
- **POST** /api/draft
    - **Input:** The extracted text from the OCR.
    - **Output:** Returns JSON with the AI generated draft text.

## How to test the API Endpoints
By going to http://localhost:8000/docs you'll see the Endpoints, you can test them there.
 
