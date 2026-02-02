import polars as pl
import sqlite3


if __name__ == "__main__":
    conn = sqlite3.connect("backup/vocab_archive.db")

    with conn as cursor:
        res = cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        table_names = [x[0] for x in res]

        for table in table_names:
            df = pl.read_database(f"SELECT * FROM {table}", cursor)
            print(df.head())

            df.write_parquet(f"data/{table}.parquet")

    # Insert in database vocabulary table
