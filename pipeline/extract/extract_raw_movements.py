import os
import pandas as pd 
from dotenv import load_dotenv
from sqlalchemy import text 
from src.db import get_db_engine


# LOAD ENV
load_dotenv()

SOURCE_PATH = os.getenv("SOURCE_PATH")
SOURCE_SYSTEM = os.getenv("SOURCE_SYSTEM")

# GET FILES LIST
def get_source_files():
    """
    Get the list of files in the source path.
    """
    files = [
        f for f in os.listdir(SOURCE_PATH) if f.endswith(".csv")
    ]
    return(sorted(files))

# GET PROCESSED FILES 
def get_processed_files(engine):
    """Get processed files from staging.processed_files table."""
    query = "SELECT file_name FROM staging.processed_files"
    df = pd.read_sql(query, engine)
    return set(df["file_name"].tolist())

# GET NEW FILES
def get_new_files(source_files, processed_files):
    """Get new files from source path."""
    return set(source_files) - processed_files

# LOAD FILE INTO STAGING RAW_MOVEMENTS TABLE
def load_file_to_staging(file_name, engine):
    """Load CSV file into staging.raw_movements."""
    file_path = os.path.join(SOURCE_PATH, file_name)
    df = pd.read_csv(file_path)

    df["source_file_name"] = file_name
    df["source_system"] = SOURCE_SYSTEM

    df.to_sql(
        name="raw_movements",
        con=engine,
        schema="staging",
        if_exists="append",
        index=False,
    )

    return len(df)


# MARK FILE AS PROCESSED
def mark_file_as_processed(file_name, engine):
    """Insert file_name into staging.processed_files."""
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO staging.processed_files (file_name, source_system) VALUES (:f, :s)"),
            {"f": file_name, "s": SOURCE_SYSTEM},
        )


# MAIN
def main():
    """Main function to extract raw movements."""
    engine = get_db_engine()
    source_files = get_source_files()
    processed_files = get_processed_files(engine)
    new_files = sorted(get_new_files(source_files, processed_files))

    if not new_files:
        print("No new files to process.")
        return

    print(f"Found {len(new_files)} new file(s) to process.")

    for file_name in new_files:
        try:
            n_rows = load_file_to_staging(file_name, engine)
            mark_file_as_processed(file_name, engine)
            print(f"  ✓ {file_name}: {n_rows} rows loaded")
        except Exception as e:
            print(f"  ✗ {file_name}: failed — {e}")

    print("Done.")

if __name__ == "__main__":
    main()