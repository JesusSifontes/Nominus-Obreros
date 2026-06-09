#importamos Sql Lite como libreria
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
    

    #tabla de Ley
    cursor_base_datos.execute("""
        CREATE TABLE IF NOT EXISTS ley_nomina (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre_regla TEXT UNIQUE,
            porcentaje REAL
        )
    """)

    # Valores parametros de legales por defecto
    lista_reglas_iniciales = [
        ('SSO', 0.04),    # Seguro Social 4%
        ('FAOV', 0.01),   # Vivienda 1%
        ('PI', 0.005),     # Paro Forzoso 0.5%
        ('BONO DE GUERRA ECONOMICA', 76500),  # bono guerra economica - ultimo mayo 2026
        ('CESTA TICKET', 20018)   # cesta ticket alimentos - ultimo mayo 2026
    ]
    
    for nombre_regla, valor_regla in lista_reglas_iniciales:
        cursor_base_datos.execute(
            "INSERT OR IGNORE INTO ley_nomina (nombre_regla, porcentaje) VALUES (?, ?)", 
            (nombre_regla, valor_regla)
        )


    
    conexion_base_datos.commit()
    conexion_base_datos.close()
    print("Base de datos y tablas verificadas correctamente.")


if __name__ == "__main__":
    crear_tablas()
