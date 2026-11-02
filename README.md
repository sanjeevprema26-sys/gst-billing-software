# ABV ASSOCIATE 

A lightweight GST billing web application built with Python and Flask.

## Features
- Add customers and products
- Generate GST invoices with automatic tax calculation
- Store data in SQLite database
- View invoice details and summary dashboard

## Tech Stack
- Python 3
- Flask
- SQLite

## Setup
1. Clone the repository
2. Create a virtual environment:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python app.py
   ```
5. Open in your browser:
   ```bash
   http://127.0.0.1:5000
   ```

## Project Structure
- `app.py` – application logic and database setup
- `templates/` – HTML pages
- `static/` – CSS and JavaScript assets
- `gst_billing.db` – SQLite database created on first run
