import os
import sys
import psycopg2

sys.path.insert(0, os.path.dirname(__file__))
from app.config import get_settings

def run():
    settings = get_settings()
    migration_file = os.path.join(os.path.dirname(__file__), "migrations", "001_initial_schema.sql")
    with open(migration_file, "r", encoding="utf-8") as f:
        sql = f.read()

    print(f"Connecting to database: {settings.database_url.split('@')[-1]} ...")
    conn = psycopg2.connect(settings.database_url)
    conn.autocommit = True
    with conn.cursor() as cur:
        cur.execute(sql)
        print("Schema migration executed successfully!")
        
        # Verify tables created
        cur.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """)
        tables = [row[0] for row in cur.fetchall()]
        print(f"Tables present in public schema: {tables}")
    conn.close()

if __name__ == "__main__":
    run()
