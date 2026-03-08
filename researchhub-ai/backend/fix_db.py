import psycopg2

# Connect as postgres superuser using trust auth (127.0.0.1 bypasses scram)
try:
    conn = psycopg2.connect(host='127.0.0.1', port=5432, dbname='ResearchHub', user='Smartbridge', password='Smartbridge123')
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("ALTER USER \"Smartbridge\" WITH PASSWORD 'Smartbridge123';")
    print("Connected as Smartbridge on 127.0.0.1 OK")
except Exception as e:
    print(f"Error: {e}")

# Verify connection with correct credentials
try:
    conn2 = psycopg2.connect(host='localhost', port=5432, dbname='ResearchHub', user='Smartbridge', password='Smartbridge123')
    print("DB connection with Smartbridge credentials: OK")
    conn2.close()
except Exception as e:
    print(f"Smartbridge login failed: {e}")
