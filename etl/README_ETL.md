# ETL / Data Warehouse Extension (Data Engineering layer)

This extends the Document AI pipeline (`pipeline_full.py`) with a Data
Engineering layer — turning the structured JSON output of the AI pipeline
into a queryable SQL data warehouse, and running analytical reports on it.
Ties directly to the CV skills: **SQL, PL/SQL, SSIS/ETL, data validation &
quality, enterprise data warehouses.**

## Pipeline stages

```
[Document AI pipeline output: structured JSON per document]
                    ↓
              EXTRACT   → pull processed documents from a staging area
                    ↓
              TRANSFORM → validate dates, normalize amounts/currency,
                           flag records needing human review
                    ↓
              LOAD      → insert into a star-schema SQL warehouse
                           (dim_document_type + fact_documents)
                    ↓
              QUERY     → run analytical SQL reports (quality dashboard,
                           financial totals, confidence monitoring)
```

## Why a star schema?
`dim_document_type` (dimension) + `fact_documents` (fact table) is the
standard data warehouse pattern: dimensions describe *what* something is,
facts record *measured events* (a processed document, its confidence
scores, its amount). This scales cleanly if more dimensions are added later
(e.g. `dim_client`, `dim_date`) without restructuring the fact table.

## Run it

```bash
python etl_pipeline.py
```

This creates `document_warehouse.db` (SQLite) and prints three reports:
1. Documents flagged for human review (quality dashboard)
2. Total amount processed, grouped by document type
3. Average classification confidence, by document type

## Adapting to production (what the CV's real stack would use)
| This demo | Production equivalent |
|---|---|
| `extract_documents()` hardcoded list | Reading from a staging folder / message queue fed by the AI pipeline |
| SQLite | Oracle or MS SQL Server (`cx_Oracle` / `pyodbc`) |
| Standalone script run manually | Scheduled **SSIS package** or Airflow DAG, running on each new batch |
| Print statements for reports | BI tool (Power BI / Tableau) connected directly to the warehouse tables |

## Explore the database directly (optional)
```bash
sqlite3 document_warehouse.db
sqlite> SELECT * FROM fact_documents;
sqlite> .quit
```
