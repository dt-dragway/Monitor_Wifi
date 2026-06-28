
import sqlite3

# Conectar a la base de datos
conn = sqlite3.connect("devices.db")
cursor = conn.cursor()

# Verificar columnas existentes
cursor.execute("PRAGMA table_info(device)")
columns = [column[1] for column in cursor.fetchall()]

if "interface" not in columns:
    print("Agregando columna 'interface'...")
    cursor.execute("ALTER TABLE device ADD COLUMN interface TEXT")
    conn.commit()
    print("Migración completada con éxito.")
else:
    print("La columna 'interface' ya existe.")

conn.close()
