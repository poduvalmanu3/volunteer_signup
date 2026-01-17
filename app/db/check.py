import psycopg2
from app.core.config import settings

def check_db_connection():
    try:
        conn = psycopg2.connect(
            host=settings.DATABASE_HOST,
            database=settings.DATABASE_NAME,
            user=settings.DATABASE_USER,
            password=settings.DATABASE_PASSWORD
        )
        conn.close()
        return True
    except Exception as e:
        print(f"Database connection error: {e}")
        return False