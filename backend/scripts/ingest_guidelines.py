"""
================================================================================
ClinSaarthi AI - Guideline Ingestion CLI Script
================================================================================
What it does:
    Scans the `data/guidelines/` folder for clinical guideline PDFs, registers
    Document entries in PostgreSQL/SQLite, chunks text, and populates the vector store.
================================================================================
"""
import os
import sys
import django

def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()
    print("Guideline Ingestion CLI ready.")

if __name__ == '__main__':
    main()
