#Importamos la libreria para interfax grafica customtkinter
import customtkinter as ctk
#Importamos libreria para ver la hora actual del PC
from datetime import datetime
#Importamos la libreria para interfax grafica tkinter
from tkinter import messagebox
#Importamos base de datos
from database import conectar
#Importamos vista o ventana para crear empleado
from empleados import ventana_registro

#Importamos parametros_ley.py , aqui estan los parametros obligatorios del trabajador
from parametros_ley import ventana_parametros

#se crean las base de datos 
from database import crear_tablas 
crear_tablas() 

#titulo de la venta principal de la interfaz grafica y se definen los parametros de la venta principal
aplicacion_principal = ctk.CTk()
aplicacion_principal.title("Nominus-Obreros v1.0.0")
aplicacion_principal.geometry("1300x650") 

#funcion que valida la confirmacion para eliminar un empleado
def eliminar_empleado(id_empleado):
    if messagebox.askyesno("Confirmar: ", f"¿Desea Eliminar el empleado de Id: {id_empleado}?"):
        conexion_base_datos = None
        cursor_base_datos = None
        try:
            conexion_base_datos = conectar()
            cursor_base_datos = conexion_base_datos.cursor()
            cursor_base_datos.execute("DELETE FROM empleados WHERE id = ?", (id_empleado,))
            conexion_base_datos.commit()
            messagebox.showinfo("El Empleado ha sido Eliminado Correctamente.")
            actualizar_listado()
        except Exception as error_eliminar:
            messagebox.showerror("ERROR: ", f"No se pudo eliminar al empleado: {error_eliminar}")
        finally:
            if cursor_base_datos: cursor_base_datos.close()
            if conexion_base_datos: conexion_base_datos.close()

#aqui definimos una validacion para que los decimales sean una  ( , ) , y no un ( . )
def formatear_pantalla_venezuela(valor_monetario):
    #funcion auxiliar idéntica a parametros_ley.py para dar formato con puntos en miles y comas en decimales (ej: 58.000,0000)
    cadena_base = f"{valor_monetario:.4f}"
    parte_entera, parte_decimal = cadena_base.split(".")
    parte_entera_con_puntos = "{:,}".format(int(parte_entera)).replace(",", ".")
    resultado_formateado = f"{parte_entera_con_puntos},{parte_decimal}"
    return resultado_formateado

#esta es la lista donde se muestran los empleados registrados o creados
def actualizar_listado():
    for componente_elemento in frame_datos_tabla.winfo_children():
        componente_elemento.destroy()

    anchos_columnas = {
        0: 40, 1: 100, 2: 120, 3: 120, 4: 100, 5: 180, 
        6: 250, 7: 110, 8: 120, 9: 130, 10: 100, 11: 100
    }

    for indice_columna, ancho_columna in anchos_columnas.items():
        frame_datos_tabla.grid_columnconfigure(indice_columna, minsize=ancho_columna)

    conexion_base_datos = None
    cursor_base_datos = None
    try:
        conexion_base_datos = conectar()
        cursor_base_datos = conexion_base_datos.cursor()
        
        cursor_base_datos.execute("""
            SELECT id, cedula, nombre, apellido, telefono, correo, 
                   direccion, fecha_ingreso, cargo, sueldo_base, fecha_nacimiento 
            FROM empleados
        """)
        lista_empleados = cursor_base_datos.fetchall()

        titulos_cabecera = ["Id", "Cédula", "Nombres", "Apellidos", "Teléfono", "Correo", 
                            "Dirección", "Fecha Ingreso", "Cargo", "Sueldo Base", "Editar", "Eliminar"]
        
        for indice_columna, texto_cabecera in enumerate(titulos_cabecera):
            ctk.CTkLabel(frame_datos_tabla, text=texto_cabecera, font=("Arial", 12, "bold")).grid(row=0, column=indice_columna, padx=5, pady=10)

        for indice_fila, datos_fila in enumerate(lista_empleados, start=1):
            id_empleado_actual = datos_fila[0]
            
            for indice_campo in range(10):
                valor_campo = datos_fila[indice_campo]
                
                #aplicamos la función auxiliar al campo sueldo con (columna de indice 9)
                texto_dato = f"{formatear_pantalla_venezuela(valor_campo)} Bs" if indice_campo == 9 else str(valor_campo)
                ajuste_linea = 200 if indice_campo == 6 else 0
                
                ctk.CTkLabel(frame_datos_tabla, text=texto_dato, wraplength=ajuste_linea).grid(row=indice_fila, column=indice_campo, padx=5, pady=5)
            
            #boton para actualizar
            # axel aqui coloca la actualizacion del empleado

            #boton para eliminar empleado
            boton_eliminar_registro = ctk.CTkButton(
                frame_datos_tabla, text="Eliminar", fg_color="#d51d1d", hover_color="#2a394a", 
                width=80, height=25, font=("Arial", 11, "bold"),
                command=lambda id_para_eliminar=id_empleado_actual: eliminar_empleado(id_para_eliminar)
            )
            boton_eliminar_registro.grid(row=indice_fila, column=11, padx=5, pady=5)
            
    except Exception as error_carga:
        ctk.CTkLabel(frame_datos_tabla, text=f"ERROR AL CARGAR: {error_carga}", text_color="red").grid(row=1, column=0, columnspan=12)
    finally:
        if cursor_base_datos: cursor_base_datos.close()
        if conexion_base_datos: conexion_base_datos.close()

#aqui inicia la interfaz grafica: donde aparece un NAV , listado de los empleados y boton para registrar empleados
marco_navegacion = ctk.CTkFrame(aplicacion_principal, height=70, corner_radius=0, fg_color="#2a394a")
marco_navegacion.pack(side="top", fill="x")

ctk.CTkLabel(marco_navegacion, text="NOMINUS-OBREROS - GRUPO SUNFLOWER & eddiemonster - v1.0.0", font=("Arial", 18, "bold"), text_color="white").pack(side="left", padx=25, pady=20)

fecha_hoy = datetime.now().strftime("%d/%m/%Y")
ctk.CTkLabel(marco_navegacion, text=f"FECHA ACTUAL: {fecha_hoy}", font=("Arial", 18), text_color="white").pack(side="right", padx=20)

marco_acciones_principales = ctk.CTkFrame(aplicacion_principal, fg_color="transparent")
marco_acciones_principales.pack(pady=30)

#boton que redirige para crear empleado
ctk.CTkButton(marco_acciones_principales, text="Registrar Empleado", command=lambda: ventana_registro(actualizar_listado), fg_color="#2fa572", width=280, height=60, font=("Arial", 16, "bold")).grid(row=0, column=0, padx=25)
#se agrega boton que redirige a parametros de ley .py
ctk.CTkButton(marco_acciones_principales, text="Parametros de ley", command=ventana_parametros, fg_color="#2fa572", width=280, height=60, font=("Arial", 16, "bold")).grid(row=0, column=2, padx=25)

#pequeño label para mostrar el listado de los empleados
ctk.CTkLabel(aplicacion_principal, text="Listado de Todos Los Empleados Activos", font=("Arial", 16, "bold")).pack(pady=(10, 5))

frame_datos_tabla = ctk.CTkScrollableFrame(aplicacion_principal, width=1250, height=350, orientation="horizontal")
frame_datos_tabla.pack(pady=10, padx=10, fill="both", expand=True)

#se llama a la funcion actualizar_listado() 
actualizar_listado()
aplicacion_principal.mainloop()