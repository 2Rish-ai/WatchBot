import psycopg2

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