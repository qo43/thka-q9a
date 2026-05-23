# Wathiq | واثق

<p align="center">
  <img src="App/Web_Interface/assets/logo.svg" alt="Wathiq logo" width="110">
</p>

<p align="center">
  <strong>AI-powered legal document review for Arabic and English files.</strong>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/FastAPI-Backend-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/Ollama-AI-111827?style=flat-square" alt="Ollama">
  <img src="https://img.shields.io/badge/Arabic%20%2B%20English-Supported-2563eb?style=flat-square" alt="Arabic and English">
</p>

## ✨ Overview

Wathiq helps users upload legal PDFs or images, extract text, detect weak legal writing, and generate clearer suggested wording.

The app supports Arabic and English documents with a simple bilingual interface.

## 🚀 Features

- Upload legal PDFs or images
- Extract text using PDF parsing and OCR
- Detect unclear parties, facts, requests, and informal wording
- Suggest stronger legal phrasing
- Arabic and English UI

## 🧠 AI Workflow

1. The document text is extracted from PDF/OCR.
2. The text is classified and reviewed.
3. Ollama generates a stronger legal draft when available.
4. If AI is offline, Wathiq falls back to rule-based review.

## 🛠 Tech Stack

Python, FastAPI, EasyOCR, PyMuPDF, OpenCV, Ollama, HTML, CSS, JavaScript

## ⚙️ Installation

```bash
git clone https://github.com/qo43/thka-q9a.git
cd thka-q9a
pip install -r requirements.txt
```

Optional AI model:

```bash
ollama pull qwen2.5:7b-instruct
```

## ▶️ Usage

```bash
python main.py
```

Open:

```text
http://127.0.0.1:8000/Web_Interface/
```

To change the AI model, edit `OLLAMA_MODEL` in `App/app.py`.

## 📸 Demo

<p align="center">
  <img src="docs/images/english-review-1.png" alt="Wathiq upload screen" width="45%">
  <img src="docs/images/english-review-2.png" alt="Wathiq review results" width="45%">
</p>

## 🔮 Future Improvements

- Add user accounts and saved review history
- Export improved drafts as PDF or DOCX
- Add more legal categories and validation rules
- Improve OCR accuracy for low-quality scans

## 👤 Author

**Adem Guedri**<br>
GitHub: [@AdemCE-eng](https://github.com/AdemCE-eng)<br>
Email: [guedriadem@gmail.com](mailto:guedriadem@gmail.com)

---

Wathiq is a prototype. Generated legal drafts should be reviewed by a legal professional before real use.
