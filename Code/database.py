import psycopg2

# H3: Connect to local PostgreSQL database (localhost) — no cloud database services are used
# H1: The system operates entirely offline; all data is stored locally
def connect_to_db():
    try:
        return psycopg2.connect(
            host="localhost",
            database="WatchBot",
            user="postgres",
            password="onepiece!1"
        )
    except psycopg2.Error as err:
        print(f"Database connection error: {err}")
        return None