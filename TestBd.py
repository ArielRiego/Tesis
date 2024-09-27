import psycopg2

try:
    conn = psycopg2.connect(
        dbname="peluqueria",
        user="postgres",
        password="123456789",
        host="localhost",
        port="5432"
    )
    print("Conexión exitosa")
except psycopg2.OperationalError as e:
    print(f"Error operativo al conectar: {e}")
except psycopg2.ProgrammingError as e:
    print(f"Error de programación al conectar: {e}")
except Exception as e:
    print(f"Error general al conectar: {e}")
finally:
    if conn:
        conn.close()
