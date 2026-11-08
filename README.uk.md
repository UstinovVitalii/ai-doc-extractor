# AI Document Extractor

[English version](README.md)

Перетворює PDF і листи (рахунки, чеки, договори) на структурований JSON.

## Проблема

Рахунки, чеки та підтвердження замовлень приходять у PDF або листами. Щоб потрапити в таблицю, CRM чи облікову систему, дані зазвичай доводиться переписувати вручну.

## Рішення

Невеликий сервіс на FastAPI. Ви завантажуєте PDF або вставляєте текст, а Gemini API повертає поля у вигляді JSON: відправник, одержувач, дати, валюта, сума та позиції. Відповідь відповідає фіксованій схемі, тому її можна одразу записати в рядок таблиці або в базу даних.

## Стек

- Python, FastAPI
- Google Gemini API (`gemini-2.5-flash`): PDF передається моделі безпосередньо, формат відповіді задається через `response_schema`
- Простий HTML/JS-фронтенд без збирання

## Результат

PDF, перетягнутий на сторінку, за кілька секунд повертається у вигляді структурованих полів.

![Перетягування PDF і отримання витягнутих полів](docs/demo.gif)

Для вигаданого рахунку з `samples/sample_invoice.pdf` сервіс повертає:

```json
{
  "document_type": "invoice",
  "sender": "ACME Cloud Services Ltd",
  "recipient": "Northwind Trading GmbH",
  "document_date": "2026-10-28",
  "due_date": "2026-11-27",
  "currency": "EUR",
  "total_amount": 1550,
  "line_items": [
    { "description": "Website maintenance (October)", "quantity": 1, "unit_price": 450, "amount": 450 },
    { "description": "Hosting, 12 months", "quantity": 12, "unit_price": 25, "amount": 300 },
    { "description": "SEO audit", "quantity": 1, "unit_price": 800, "amount": 800 }
  ],
  "summary": "This invoice from ACME Cloud Services Ltd to Northwind Trading GmbH is for website maintenance, hosting, and an SEO audit, totaling EUR 1,550.00 due by November 27, 2026."
}
```

Текстовий рахунок українською (суми в гривнях із комою, дата словами) теж прочитано правильно. Назви компаній і позицій лишаються мовою оригіналу, а поле `summary` повертається англійською.

Поки що перевірено лише на згенерованих документах: PDF-рахунок, лист і текстовий рахунок українською. Скани та нестандартні макети слід перевірити на реальних документах, перш ніж покладатися на результат.

## Запуск

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

python -m pip install -r requirements.txt
copy .env.example .env       # потім вкажіть GEMINI_API_KEY у .env
uvicorn main:app --reload
```

Відкрийте http://127.0.0.1:8000 і спробуйте з `samples/sample_invoice.pdf`.

## API

- `POST /extract/pdf`: multipart-поле `file`, PDF до 14 МБ
- `POST /extract/text`: поле форми `text`

Обидва повертають JSON із полями `document_type`, `sender`, `recipient`, `document_date`, `due_date`, `currency`, `total_amount`, `line_items` і `summary`.

## Примітки

- PDF передається моделі як є, тому окремого кроку OCR немає.
- Режим міркування вимкнено (`thinking_budget=0`). Для вилучення даних він не потрібен, а так дешевше і швидше.
- Схема визначає форму відповіді, а не правильність значень. Перевіряйте суми, перш ніж використовувати їх у фінансових операціях.

## Використання в реальному процесі

- Записувати результат у Google Sheets, CRM або базу даних замість того, щоб повертати його у відповіді.
- Використовувати окрему схему для кожного типу документів, якщо вони сильно відрізняються (замовлення на закупівлю та договори).
- Запускати за розкладом для поштової скриньки або папки на Drive.
