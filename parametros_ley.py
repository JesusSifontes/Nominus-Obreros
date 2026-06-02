#importamos interfaz
import customtkinter as ctk
#importamos tkinter
from tkinter import messagebox
#importamos dase de datos.py
from database import conectar


def obtener_parametros():
    #todas las reglas y valores de la tabla ley_nomina.py
    conexion_base_datos = conectar()
    cursor_base_datos = conexion_base_datos.cursor()
    try:
        cursor_base_datos.execute("SELECT nombre_regla, porcentaje FROM ley_nomina")
        lista_reglas_ley = cursor_base_datos.fetchall()
        return lista_reglas_ley
    except Exception as error_lectura:
        messagebox.showerror(f"Error: No se pudieron cargar los parámetros: {error_lectura}")
        return []
    finally:
        cursor_base_datos.close()
        conexion_base_datos.close()

def guardar_parametro(nombre_regla, nombre_completo_regla, nuevo_valor_texto, ventana_origen, callback_recargar):
    #aqui se actualiza el valor en la Base de datos validando minimos, maximos, comas y redondeando a 4 decimales
    if not nuevo_valor_texto.strip():
        messagebox.showwarning("Advertencia: El valor no puede estar vacío.")
        return

    try:
        #convertimos la coma en punto para que Python y SQLite puedan procesar el flotante
        valor_flotante = float(nuevo_valor_texto.replace(",", "."))
        #redondear estrictamente a 4 decimales antes de guardar
        valor_para_guardar = round(valor_flotante, 4)
    except ValueError:
        messagebox.showerror("Error: Por favor, introduce un número válido.")
        return

    #controlador de minimos y maximos segun el tipo de parametros
    if nombre_regla in ['SSO', 'FAOV', 'PI']:
        minimo_permitido, maximo_permitido = 0.0000, 0.2000
        mensaje_rango_legal = "Debe estar entre 0,0000 (0%) y 0,2000 (20%)"
    else:
        minimo_permitido, maximo_permitido = 0.0100, 999999.9999
        mensaje_rango_legal = "Debe estar entre 0,0100 Bs. y 999.999,9999 Bs."

    if not (minimo_permitido <= valor_para_guardar <= maximo_permitido):
        messagebox.showwarning(f"Rango Inválido: El valor para '{nombre_completo_regla}' {mensaje_rango_legal}.")
        return

    conexion_base_datos = conectar()
    cursor_base_datos = conexion_base_datos.cursor()
    try:
        cursor_base_datos.execute(
            "UPDATE ley_nomina SET porcentaje = ? WHERE nombre_regla = ?", 
            (valor_para_guardar, nombre_regla)
        )
        conexion_base_datos.commit()
        messagebox.showinfo("Éxito", f"'{nombre_completo_regla}' actualizado correctamente.")
        ventana_origen.destroy()
        callback_recargar() #reabre la ventana principal de parámetros para refrescar los datos
    except Exception as error_escritura:
        messagebox.showerror("Error", f"No se pudo actualizar el parámetro: {error_escritura}")
    finally:
        cursor_base_datos.close()
        conexion_base_datos.close()

def validar_entrada_coma(texto_futuro_campo):
    #permite únicamente números enteros y una sola COMA como decimal.
    #se Bloquea el punto (.) y restringe estrictamente a usuario un maximo de 4 DDecimlaes.
    if texto_futuro_campo == "":
        return True
    
    #bloquea el punto de raíz
    if "." in texto_futuro_campo:
        return False

    #validar que solo contenga dígitos y como máximo una sola coma
    if texto_futuro_campo.count(',') <= 1 and texto_futuro_campo.replace(',', '').isdigit():
        # Si ya tiene una coma, validar cuántos dígitos hay a la derecha
        if ',' in texto_futuro_campo:
            parte_entera, parte_decimal = texto_futuro_campo.split(',')
            if len(parte_decimal) > 4:
                return False #se bloquea la escritura si intentan poner un 5to decimal (OJO solo se permiten 4 decimales)
        return True
        
    return False

def formatear_pantalla_venezuela(valor_numerico):
    
    #Transforma un float de la Base de Datos: ejemplo 12500.5000  a un formato legible con separadores de miles en puntos y decimales en comas (12.500,5000)

    cadena_base = f"{valor_numerico:.4f}"
    parte_entera, parte_decimal = cadena_base.split(".")
    parte_entera_con_puntos = "{:,}".format(int(parte_entera)).replace(",", ".")
    resultado_formateado = f"{parte_entera_con_puntos},{parte_decimal}"
    return resultado_formateado

def abrir_ventana_edicion(nombre_regla, nombre_completo_regla, valor_actual_regla, callback_recargar):
    #abre una pequeña ventana emergente para modificar los parametro seleccionado
    ventana_emergente_edicion = ctk.CTkToplevel()
    ventana_emergente_edicion.title(f"Editar {nombre_completo_regla}")
    ventana_emergente_edicion.geometry("450x250") 
    ventana_emergente_edicion.grab_set() 
    ventana_emergente_edicion.resizable(False, False)

    ctk.CTkLabel(
        ventana_emergente_edicion, 
        text=f"Modificar valor para:\n{nombre_completo_regla}", 
        font=("Arial", 14, "bold"),
        justify="center"
    ).pack(pady=15)

    if nombre_regla in ['SSO', 'FAOV', 'PI']:
        texto_ayuda_rango = "Rango: 0,0000 a 0,2000 (Ej: 0,0400 para el 4% - Máx 4 dec.)"
    else:
        texto_ayuda_rango = "Rango: 0,0100 a 999.999,9999 Bs. (Máx 4 dec.)"
        
    ctk.CTkLabel(ventana_emergente_edicion, text=texto_ayuda_rango, font=("Arial", 11), text_color="gray").pack()

    #reegistramos la validación estricta con una coma y sus 4 decimales
    comando_validacion_entrada = (ventana_emergente_edicion.register(validar_entrada_coma), "%P")

    cuadro_entrada_valor = ctk.CTkEntry(
        ventana_emergente_edicion, 
        width=200, 
        font=("Arial", 14),
        validate="key",           
        validatecommand=comando_validacion_entrada      
    )
    
    #al cargar el valor en la caja de input de texto para editar, lo convertimos a formato con COMA (ej: "58000,0000")
    valor_inicial_editable = f"{valor_actual_regla:.4f}".replace(".", ",")
    cuadro_entrada_valor.insert(0, valor_inicial_editable)
    cuadro_entrada_valor.pack(pady=10)

    #frame contenedor para ordenar los botones de la edicion de forma horizontal
    marco_botones_edicion = ctk.CTkFrame(ventana_emergente_edicion, fg_color="transparent")
    marco_botones_edicion.pack(pady=10)

    #boton guardar: en color fg_color="#2fa572"
    boton_guardar_cambios = ctk.CTkButton(
        marco_botones_edicion, 
        text="Guardar Cambios", 
        fg_color="#2fa572",
        width=140,
        font=("Arial", 12, "bold"),
        command=lambda: guardar_parametro(nombre_regla, nombre_completo_regla, cuadro_entrada_valor.get(), ventana_emergente_edicion, callback_recargar)
    )
    boton_guardar_cambios.grid(row=0, column=0, padx=10)

    #boton cancelar en color rojo fg_color="#a52f2f"
    boton_cancelar_edicion = ctk.CTkButton(
        marco_botones_edicion, 
        text="Cancelar", 
        fg_color="#a52f2f",
        width=140,
        font=("Arial", 12, "bold"),
        command=ventana_emergente_edicion.destroy
    )
    boton_cancelar_edicion.grid(row=0, column=1, padx=10)

def ventana_parametros():
    #se genera la ventana principal donde se muestran los parametros de ley
    ventana_principal_parametros = ctk.CTkToplevel()
    ventana_principal_parametros.title("Parámetros de Ley - Configuración de Nómina")
    ventana_principal_parametros.geometry("820x480") 
    ventana_principal_parametros.grab_set()
    ventana_principal_parametros.resizable(False, False)

    marco_encabezado_superior = ctk.CTkFrame(ventana_principal_parametros, height=60, fg_color="#2a394a", corner_radius=0)
    marco_encabezado_superior.pack(fill="x", side="top")
    
    ctk.CTkLabel(
        marco_encabezado_superior, 
        text="PARÁMETROS DE LEY VIGENTES", 
        font=("Arial", 16, "bold"), 
        text_color="white"
    ).pack(pady=15)

    marco_contenido_tabla = ctk.CTkFrame(ventana_principal_parametros, fg_color="transparent")
    marco_contenido_tabla.pack(fill="both", expand=True, padx=20, pady=20)

    def recargar_ventana():
        ventana_principal_parametros.destroy()
        ventana_parametros()

    #diccionario en traduccion: solo para mostrar nombres completos en pantalla
    nombres_completos_reglas = {
        'SSO': 'Seguro Social Obligatorio (SSO)',
        'FAOV': 'Fondo de Ahorro Obligatorio para la Vivienda (FAOV)',
        'PI': 'Paro Forzoso / Pérdida de Empleo (PI)',
        'BONO DE GUERRA ECONOMICA': 'Bono de Guerra Económica',
        'CESTA TICKET': 'Cesta Ticket'
    }

    lista_reglas_obtenidas = obtener_parametros()

    #encabezados de la tabla
    ctk.CTkLabel(marco_contenido_tabla, text="Concepto / Regla Legal", font=("Arial", 13, "bold")).grid(row=0, column=0, padx=15, pady=10, sticky="w")
    ctk.CTkLabel(marco_contenido_tabla, text="Monto en Bs.", font=("Arial", 13, "bold")).grid(row=0, column=1, padx=15, pady=10, sticky="w")
    ctk.CTkLabel(marco_contenido_tabla, text="Porcentaje", font=("Arial", 13, "bold")).grid(row=0, column=2, padx=15, pady=10, sticky="w")
    ctk.CTkLabel(marco_contenido_tabla, text="Acción", font=("Arial", 13, "bold")).grid(row=0, column=3, padx=15, pady=10)

    for indice_fila, (nombre_regla, valor_porcentaje) in enumerate(lista_reglas_obtenidas, start=1):
        nombre_pantalla_regla = nombres_completos_reglas.get(nombre_regla, nombre_regla)
        valor_formateado_pantalla = formatear_pantalla_venezuela(valor_porcentaje)
        
        #logica de division con terminacion en Bs. fija en la columna 1
        if nombre_regla in ['SSO', 'FAOV', 'PI']:
            porcentaje_calculado_usuario = f"{valor_porcentaje * 100:.2f}".replace(".", ",")
            texto_columna_monto = f"{valor_formateado_pantalla} Bs."
            texto_columna_porcentaje = f"{porcentaje_calculado_usuario}%"
        else:
            texto_columna_monto = f"{valor_formateado_pantalla} Bs."
            texto_columna_porcentaje = "-"

        etiqueta_nombre_regla = ctk.CTkLabel(marco_contenido_tabla, text=nombre_pantalla_regla, font=("Arial", 12, "bold"))
        etiqueta_nombre_regla.grid(row=indice_fila, column=0, padx=15, pady=8, sticky="w")

        etiqueta_monto_regla = ctk.CTkLabel(marco_contenido_tabla, text=texto_columna_monto, font=("Arial", 12))
        etiqueta_monto_regla.grid(row=indice_fila, column=1, padx=15, pady=8, sticky="w")

        etiqueta_porcentaje_regla = ctk.CTkLabel(marco_contenido_tabla, text=texto_columna_porcentaje, font=("Arial", 12))
        etiqueta_porcentaje_regla.grid(row=indice_fila, column=2, padx=15, pady=8, sticky="w")

        #boton modifica en color azul fg_color="#2f6ba5"
        boton_modificar_parametro = ctk.CTkButton(
            marco_contenido_tabla, 
            text="Modificar", 
            width=100,
            height=25,
            fg_color="#2f6ba5",
            font=("Arial", 11, "bold"),
            command=lambda n=nombre_regla, np=nombre_pantalla_regla, v=valor_porcentaje: abrir_ventana_edicion(n, np, v, recargar_ventana)
        )
        boton_modificar_parametro.grid(row=indice_fila, column=3, padx=15, pady=8)

    #boton cerrar ventana principal en color rojo fg_color="#a52f2f" 
    boton_cerrar_ventana_principal = ctk.CTkButton(
        ventana_principal_parametros, 
        text="Cerrar Ventana", 
        fg_color="#a52f2f", 
        font=("Arial", 12, "bold"),
        command=ventana_principal_parametros.destroy
    )
    boton_cerrar_ventana_principal.pack(pady=15)