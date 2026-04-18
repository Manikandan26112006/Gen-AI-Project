"""
Builds the initial ChromaDB index for the Faculty Performance System.
Reads all faculty data from SQLite and pushes it to ChromaDB.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from backend.data_loader import load_all_data
from vector_db.chroma_store import build_index

def main():
    print("⏳ Loading faculty data from SQLite...")
    df = load_all_data()
    if df.empty:
        print("❌ No data found in SQLite. Please run database/init_database.py first.")
        return

    print(f"📦 Found {len(df)} faculty records. Building ChromaDB index...")
    build_index(df)
    print("✅ Vector database (RAG) initialized successfully!")

if __name__ == "__main__":
    main()
