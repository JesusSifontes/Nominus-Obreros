#importamos Sql Lite como klibreria
import sqlite3

def conectar():
    # Establece la conexión con la base de datos SQLite
    return sqlite3.connect("nominus_data.db")

#se crean las tablas automaticamente : en tal caso de no existir
def crear_tablas():
    conexion_base_datos = conectar()
    cursor_base_datos = conexion_base_datos.cursor()
    
    #tabla de Empleados
    cursor_base_datos.execute("""
        CREATE TABLE IF NOT EXISTS empleados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cedula TEXT UNIQUE NOT NULL,
            nombre TEXT NOT NULL,
            apellido TEXT NOT NULL,
            telefono TEXT,
            correo TEXT,
            direccion TEXT,
            fecha_nacimiento TEXT,  
            fecha_ingreso TEXT,
            cargo TEXT,
            sueldo_base REAL NOT NULL
        )
    """)
    
    
    conexion_base_datos.commit()
    conexion_base_datos.close()
    print("Base de datos y tablas verificadas correctamente.")


if __name__ == "__main__":
    crear_tablas()