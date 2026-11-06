import json
import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import errors, types

load_dotenv()

app = FastAPI(title="AI Document Extractor")
app.mount("/static", StaticFiles(directory="static"), name="static")

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

MODEL = "gemini-2.5-flash"
# Gemini limits the whole inline request (file + text + schema) to about 20 MB,
# and base64 adds roughly 33%, so the PDF limit is set well below that.
MAX_PDF_BYTES = 14 * 1024 * 1024

EXTRACTION_INSTRUCTION = (
    "Extract structured data from this business document (invoice, receipt, "
    'contract, or email) as JSON matching the schema. Use an empty string "" '
    "for text fields that are not present, 0 for missing numbers, and an "
    "empty array if there are no line items."
)

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "document_type": {
            "type": "STRING",
            "description": "e.g. invoice, receipt, contract, email, letter",
        },
        "sender": {"type": "STRING"},
        "recipient": {"type": "STRING"},
        "document_date": {
            "type": "STRING",
            "description": "ISO 8601 (YYYY-MM-DD) if present",
        },
        "due_date": {
            "type": "STRING",
            "description": "ISO 8601 (YYYY-MM-DD) if present",
        },
        "currency": {
            "type": "STRING",
            "description": "ISO 4217 code, e.g. USD, EUR",
        },
        "total_amount": {"type": "NUMBER"},
        "line_items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "description": {"type": "STRING"},
                    "quantity": {"type": "NUMBER"},
                    "unit_price": {"type": "NUMBER"},
                    "amount": {"type": "NUMBER"},
                },
                "required": ["description", "quantity", "unit_price", "amount"],
            },
        },
        "summary": {
            "type": "STRING",
            "description": "One-sentence plain-language summary",
        },
    },
    "required": [
        "document_type",
        "sender",
        "recipient",
        "document_date",
        "due_date",
        "currency",
        "total_amount",
        "line_items",
        "summary",
    ],
}


def extract_from_content(parts: list) -> dict:
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=parts,
            config=types.GenerateContentConfig(
                system_instruction=EXTRACTION_INSTRUCTION,
                response_mime_type="application/json",
                response_schema=RESPONSE_SCHEMA,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
            ),
        )
    except errors.ClientError as e:
        if e.code == 429:
            raise HTTPException(
                status_code=429,
                detail="Rate limited by the AI provider, try again shortly",
            )
        raise HTTPException(status_code=502, detail=f"AI provider error: {e.message}")
    except errors.ServerError as e:
        raise HTTPException(status_code=502, detail=f"AI provider error: {e.message}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    if not response.text:
        raise HTTPException(status_code=502, detail="Model did not return structured data")
    return json.loads(response.text)


@app.get("/")
def index():
    return HTMLResponse(Path("static/index.html").read_text(encoding="utf-8"))


@app.post("/extract/pdf")
async def extract_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    pdf_bytes = await file.read()
    if len(pdf_bytes) > MAX_PDF_BYTES:
        raise HTTPException(status_code=400, detail="File too large (14MB limit)")

    parts = [
        types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf"),
        "Extract the structured data from this document.",
    ]
    return JSONResponse(extract_from_content(parts))


@app.post("/extract/text")
async def extract_text(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    parts = [f"Extract the structured data from this document:\n\n{text}"]
    return JSONResponse(extract_from_content(parts))
