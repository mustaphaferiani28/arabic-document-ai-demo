"""
ETL Layer - Data Engineering extension to the Document AI pipeline
Extract (from processed document JSON) -> Transform (validate/clean) -> Load (SQL warehouse) -> Query

This demonstrates the Data Engineering side of the CV: SQL, ETL, data warehousing,
data validation/quality, applied on top of the Document AI outputs.

In production, replace:
- extract_documents() -> reading from a real staging folder / message queue /
  the actual output of the classification+NER pipeline
- sqlite3 -> Oracle / MS SQL Server (as listed in the CV), using cx_Oracle / pyodbc
- This standalone script -> orchestrated via SSIS or Airflow for scheduled runs
"""
import sqlite3
import json
import re
import os

# ---------- CONFIG (from environment variables — Docker-friendly pattern) ----------
# In production, DB_PATH would point to a mounted volume, and connection details
# for Oracle/MS SQL would also come from env vars (never hardcoded in code).
DB_PATH = os.environ.get("DB_PATH", "document_warehouse.db")
REVIEW_THRESHOLD = float(os.environ.get("REVIEW_THRESHOLD", "0.80"))


# ---------- EXTRACT ----------
def extract_documents():
    """
    Simulates extracting multiple processed documents from a staging area.
    In production: this reads the structured_output.json produced by the
    Document AI pipeline (pipeline_full.py) for each processed document.
    """
    return [
        {"document_type": "invoice", "classification_confidence": 0.94,
         "fields": {"invoice_number": {"value": "INY-2026-0472", "confidence": 0.65},
                    "date": {"value": "2026-08-15", "confidence": 0.98},
                    "amount": {"value": "1250.00 TND", "confidence": 0.95}},
         "needs_human_review": True, "source_file": "invoice_0472.pdf"},
        {"document_type": "invoice", "classification_confidence": 0.91,
         "fields": {"invoice_number": {"value": "INV-2026-0511", "confidence": 0.92},
                    "date": {"value": "2026-08-10", "confidence": 0.97},
                    "amount": {"value": "890.00 TND", "confidence": 0.93}},
         "needs_human_review": False, "source_file": "invoice_0511.pdf"},
        {"document_type": "contract", "classification_confidence": 0.88,
         "fields": {"invoice_number": {"value": None, "confidence": 0.0},
                    "date": {"value": "2026-01-01", "confidence": 0.90},
                    "amount": {"value": None, "confidence": 0.0}},
         "needs_human_review": False, "source_file": "contract_2026.pdf"},
    ]


# ---------- TRANSFORM ----------
def transform_documents(raw_docs):
    """
    Data quality / validation rules applied before loading:
    - Normalize amount into numeric value + currency
    - Validate date format (YYYY-MM-DD)
    - Flag records for human review (OCR confidence OR failed validation)
    """
    clean_records = []
    for doc in raw_docs:
        amount_raw = doc['fields']['amount']['value']
        amount_numeric, currency = None, None
        if amount_raw:
            match = re.match(r'([\d.]+)\s*(\w+)', amount_raw)
            if match:
                amount_numeric, currency = float(match.group(1)), match.group(2)

        date_val = doc['fields']['date']['value']
        date_valid = bool(re.match(r'^\d{4}-\d{2}-\d{2}$', date_val)) if date_val else False

        clean_records.append({
            "source_file": doc['source_file'],
            "document_type": doc['document_type'],
            "classification_confidence": doc['classification_confidence'],
            "invoice_number": doc['fields']['invoice_number']['value'],
            "invoice_number_confidence": doc['fields']['invoice_number']['confidence'],
            "date": date_val,
            "date_valid": date_valid,
            "amount_numeric": amount_numeric,
            "currency": currency,
            "needs_human_review": doc['needs_human_review'] or not date_valid,
        })
    return clean_records


def apply_confidence_threshold(records, threshold=REVIEW_THRESHOLD):
    """Re-evaluate the review flag using a configurable confidence threshold
    (instead of the fixed 0.80 baked into the original AI pipeline output)."""
    for r in records:
        low_class_conf = r['classification_confidence'] < threshold
        # Only check invoice_number confidence when the field is actually expected
        # (a contract legitimately has no invoice number, so confidence=0 there is fine)
        low_field_conf = r['invoice_number'] is not None and r['invoice_number_confidence'] < threshold
        if low_class_conf or low_field_conf:
            r['needs_human_review'] = True
    return records


# ---------- LOAD ----------
def load_to_warehouse(records, db_path=DB_PATH):
    """
    Loads transformed records into a simple star schema:
      dim_document_type : dimension table (document type lookup)
      fact_documents     : fact table (one row per processed document)

    In production: swap sqlite3 for Oracle/MS SQL Server (cx_Oracle / pyodbc),
    and this would typically run as a scheduled SSIS package or Airflow DAG.
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS fact_documents")
    cur.execute("DROP TABLE IF EXISTS dim_document_type")

    cur.execute("""
        CREATE TABLE dim_document_type (
            type_id INTEGER PRIMARY KEY AUTOINCREMENT,
            type_name TEXT UNIQUE NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE fact_documents (
            doc_id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_file TEXT NOT NULL,
            type_id INTEGER NOT NULL,
            classification_confidence REAL,
            invoice_number TEXT,
            invoice_number_confidence REAL,
            doc_date TEXT,
            date_valid INTEGER,
            amount_numeric REAL,
            currency TEXT,
            needs_human_review INTEGER,
            loaded_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (type_id) REFERENCES dim_document_type(type_id)
        )
    """)

    for r in records:
        cur.execute("INSERT OR IGNORE INTO dim_document_type (type_name) VALUES (?)", (r['document_type'],))
        cur.execute("SELECT type_id FROM dim_document_type WHERE type_name = ?", (r['document_type'],))
        type_id = cur.fetchone()[0]

        cur.execute("""
            INSERT INTO fact_documents
            (source_file, type_id, classification_confidence, invoice_number,
             invoice_number_confidence, doc_date, date_valid, amount_numeric,
             currency, needs_human_review)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (r['source_file'], type_id, r['classification_confidence'], r['invoice_number'],
              r['invoice_number_confidence'], r['date'], int(r['date_valid']), r['amount_numeric'],
              r['currency'], int(r['needs_human_review'])))

    conn.commit()
    conn.close()
    print(f"LOAD: {len(records)} records loaded into {db_path}")


# ---------- QUERY / REPORTING ----------
def run_reports(db_path=DB_PATH):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    print("\n--- Documents needing human review ---")
    cur.execute("""
        SELECT f.source_file, d.type_name, f.classification_confidence, f.invoice_number_confidence
        FROM fact_documents f JOIN dim_document_type d ON f.type_id = d.type_id
        WHERE f.needs_human_review = 1
    """)
    for row in cur.fetchall():
        print(f"  {row[0]} | type={row[1]} | class_conf={row[2]} | field_conf={row[3]}")

    print("\n--- Total amount processed, by document type ---")
    cur.execute("""
        SELECT d.type_name, COUNT(*), SUM(f.amount_numeric), f.currency
        FROM fact_documents f JOIN dim_document_type d ON f.type_id = d.type_id
        WHERE f.amount_numeric IS NOT NULL
        GROUP BY d.type_name, f.currency
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: {row[1]} docs, total = {row[2]} {row[3]}")

    print("\n--- Average classification confidence, by document type ---")
    cur.execute("""
        SELECT d.type_name, ROUND(AVG(f.classification_confidence), 3)
        FROM fact_documents f JOIN dim_document_type d ON f.type_id = d.type_id
        GROUP BY d.type_name
    """)
    for row in cur.fetchall():
        print(f"  {row[0]}: avg confidence = {row[1]}")

    conn.close()


if __name__ == "__main__":
    print(f"CONFIG: DB_PATH={DB_PATH} | REVIEW_THRESHOLD={REVIEW_THRESHOLD}")

    raw = extract_documents()
    print(f"EXTRACT: {len(raw)} documents pulled from staging area")

    transformed = transform_documents(raw)
    transformed = apply_confidence_threshold(transformed)
    print(f"TRANSFORM: {len(transformed)} records validated and cleaned")

    load_to_warehouse(transformed)

    run_reports()
