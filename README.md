# AI Document Extractor

Turns PDFs and emails (invoices, receipts, contracts) into structured JSON.

## Problem

Invoices, receipts and order confirmations arrive as PDFs or emails. Getting the data into a spreadsheet, CRM or accounting tool usually means copying it by hand.

## Solution

A small FastAPI service. Upload a PDF or paste text, and the Gemini API returns the fields as JSON: sender, recipient, dates, currency, total and line items. The response follows a fixed schema, so it can go straight into a spreadsheet row or a database.

## Stack

- Python, FastAPI
- Google Gemini API (`gemini-2.5-flash`): the PDF is sent to the model directly, the output is constrained with `response_schema`
- Plain HTML/JS frontend, no build step

## Setup

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

python -m pip install -r requirements.txt
copy .env.example .env       # then set GEMINI_API_KEY in .env
uvicorn main:app --reload
```

Open http://127.0.0.1:8000

## API

- `POST /extract/pdf`: multipart field `file`, PDF up to 14 MB
- `POST /extract/text`: form field `text`

Both return JSON with `document_type`, `sender`, `recipient`, `document_date`, `due_date`, `currency`, `total_amount`, `line_items` and `summary`.

## Notes

- The PDF goes to the model as is, so there is no separate OCR step.
- Thinking is turned off (`thinking_budget=0`). Extraction does not need it, and it keeps cost and latency down.
- The schema fixes the shape of the response, not the correctness of the values. Check the numbers before using them for anything financial.

## Using it in a real workflow

- Write the result to Google Sheets, a CRM or a database instead of returning it.
- Use a separate schema for each document type if the documents differ a lot (purchase orders vs. contracts).
- Run it on a schedule against an inbox or a Drive folder.
