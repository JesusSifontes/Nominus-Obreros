#Importamos la libreria para interfax grafica customtkinter
import customtkinter as ctk
#Importamos la libreria para interfax grafica tkinter
from tkinter import messagebox
#Importamos libreria para las expresiones regulares -> validar los campos input
import re
#Importamos base de datos
from database import conectar

# aqui se valida todos los input de la ventana de CREAR empleados
def validar_inputs(texto_ingresado, tipo_validacion):
    if texto_ingresado == "": return True
    
    #campo cedula: solo números
    if tipo_validacion == "cedula":
        if len(texto_ingresado) > 10: return False
        return texto_ingresado.isdigit()
        
    #campo nombres,apellidos y cargos: solo letras y espacios
    if tipo_validacion == "letras":
        if len(texto_ingresado) > 20: return False
        return all(caracter.isalpha() or caracter.isspace() for caracter in texto_ingresado)
        
    #campo correo electronico: tiene que tener el @
    if tipo_validacion == "correo":
        return len(texto_ingresado) <= 50

    #campo direccion: solo letras, números enteros y espacios.
    if tipo_validacion == "direccion":
        if len(texto_ingresado) > 50: return False
        return all(caracter.isalnum() or caracter.isspace() for caracter in texto_ingresado)
    
    #campo sueldo: solo con coma (,) y solo numeros 
    if tipo_validacion == "sueldo": 
        if "." in texto_ingresado:
            return False
        if len(texto_ingresado) > 11:
            return False
        if texto_ingresado.count(',') <= 1 and texto_ingresado.replace(',', '').isdigit():
            if ',' in texto_ingresado:
                parte_entera, parte_decimal = texto_ingresado.split(',')
                if len(parte_decimal) > 4:
                    return False 
            return True
        return False

    #campo fechas: solo se permiten numeros y barras '/' - solo en formato que se permite es (DD/MM/AAAA)
    if tipo_validacion == "fecha":
        if len(texto_ingresado) > 10: return False
        return all(caracter.isdigit() or caracter == '/' for caracter in texto_ingresado)

    #campo telefono: solo numeros enteros
    if tipo_validacion == "numeros":
        if len(texto_ingresado) > 11: return False
        return texto_ingresado.isdigit()

    return True

#funcion para guardar empleados
def guardar_empleado(lista_campos_entradas, ventana, callback_actualizar):
    """REALIZA EL INSERT EN LA BASE DE DATOS"""
    valores_extraidos = [campo.get().strip() for campo in lista_campos_entradas]
    
    (cedula, nombre, apellido, telefono, correo, cargo, 
     fecha_nacimiento, fecha_ingreso, sueldo_texto, direccion) = valores_extraidos

    #aqui se evalua que los campos no esten vacios
    if not all(valores_extraidos):
        messagebox.showwarning("Error", "Todos los campos son obligatorios.")
        return

    #validacion del campo Cedula: minimo 5 y maximo 10
    if not (5 <= len(cedula) <= 10):
        messagebox.showwarning("Error", "Cédula: debe tener entre 5 y 10 dígitos numéricos (sin puntos ni comas).")
        return

    #valicacion de telefono tiene que tener exactamente 11 caracteres solo numericos
    if len(telefono) != 11:
        messagebox.showwarning("Error", "Teléfono: debe tener exactamente 11 caracteres.")
        return

    #validacion de los campos nombres y apellidos: minimo 2 y maximo 20
    if not (2 <= len(nombre) <= 20) or not (2 <= len(apellido) <= 20):
        messagebox.showwarning("Error", "Nombres y Apellidos: deben tener entre 2 y 20 caracteres (solo letras).")
        return

    #validacion del campo correo electronico: minimo 14 y maximo 50 caracteres , ademas exige el @ obligatoriamente
    if not (14 <= len(correo) <= 50) or "@" not in correo:
        messagebox.showwarning("Error", "Correo Electrónico: debe tener entre 14 y 50 caracteres y contener un '@' válido.")
        return

    #validacion del campo cargo: minimo 3 y maximo 15 caracteres
    if not (3 <= len(cargo) <= 15):
        messagebox.showwarning("Error", "Cargo: debe tener entre 3 y 15 letras.")
        return

    #validacion del campos direccion: minimo 5 y maximo 50 caracteres
    if not (5 <= len(direccion) <= 50):
        messagebox.showwarning("Error", "Dirección: debe tener entre 5 y 50 caracteres.")
        return

    #aqui usamos expresion regular para las fechas
    formato_fecha = r"^\d{2}/\d{2}/\d{4}$"
    if not re.match(formato_fecha, fecha_nacimiento) or not re.match(formato_fecha, fecha_ingreso):
        messagebox.showwarning("Error", "Fechas: deben cumplir el formato DD/MM/AAAA.")
        return
    
    #validador de sueldo: maximo 6 + 4 decimales , un total de 10 caracteres numericos flotantes
    try:
        sueldo_decimal = float(sueldo_texto.replace(",", "."))
        if not (0.01 <= sueldo_decimal <= 999999.9999):
            messagebox.showwarning("Error", "Sueldo: debe estar entre 0,01 y 999999,9999.")
            return
    except ValueError:
        messagebox.showwarning("Error", "Sueldo: debe ser un valor numérico válido usando coma para los decimales.")
        return

    try:
        conexion_base_datos = conectar()
        cursor_base_datos = conexion_base_datos.cursor()
        
        cursor_base_datos.execute("""
            INSERT INTO empleados (
                cedula, nombre, apellido, telefono, correo, 
                cargo, fecha_nacimiento, fecha_ingreso, sueldo_base, direccion
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cedula, nombre.lower(), apellido.lower(), telefono, correo.lower(), cargo.lower(), 
              fecha_nacimiento, fecha_ingreso, round(sueldo_decimal, 4), direccion))
        
        conexion_base_datos.commit()
        conexion_base_datos.close()
        
        messagebox.showinfo("Éxito", f"Empleado {nombre.upper()} {apellido.upper()} registrado.")
        ventana.destroy()
        
        if callback_actualizar:
            callback_actualizar()

    except Exception as error:
        messagebox.showerror("Error", f"Error de base de datos: {error}")

#este es el apartado de ventana para registrar un empleado
def ventana_registro(callback_actualizar=None):
    ventana_registro_formulario = ctk.CTkToplevel()
    ventana_registro_formulario.title("Registro de Personal - Nominus-Obreros")
    ventana_registro_formulario.geometry("900x580") 
    ventana_registro_formulario.resizable(False, False)
    ventana_registro_formulario.grab_set()

    #registro de funciones de validaciones
    validacion_cedula = ventana_registro_formulario.register(lambda P: validar_inputs(P, "cedula"))
    validacion_letras = ventana_registro_formulario.register(lambda P: validar_inputs(P, "letras"))
    validacion_correo = ventana_registro_formulario.register(lambda P: validar_inputs(P, "correo"))
    validacion_direccion = ventana_registro_formulario.register(lambda P: validar_inputs(P, "direccion"))
    validacion_telefono = ventana_registro_formulario.register(lambda P: validar_inputs(P, "numeros")) 
    validacion_sueldo = ventana_registro_formulario.register(lambda P: validar_inputs(P, "sueldo"))
    validacion_fecha = ventana_registro_formulario.register(lambda P: validar_inputs(P, "fecha"))

    #ventana del formulario para crear empleado nuevo
    ctk.CTkLabel(ventana_registro_formulario, text="Formulario para Registrar Empleados", font=("Arial", 18, "bold")).pack(pady=(20, 10))

    marco_formulario = ctk.CTkFrame(ventana_registro_formulario, fg_color="transparent")
    marco_formulario.pack(fill="x", padx=30) 
    marco_formulario.grid_columnconfigure(0, weight=1)
    marco_formulario.grid_columnconfigure(1, weight=1)

    def crear_campo(etiqueta_texto, fila, columna, tipo_validacion=None, sugerencia_texto=""):
        etiqueta = ctk.CTkLabel(marco_formulario, text=etiqueta_texto, font=("Arial", 12, "bold"))
        etiqueta.grid(row=fila, column=columna, sticky="w", padx=25, pady=(8, 0))
        campo_entrada = ctk.CTkEntry(marco_formulario, width=380, height=35, placeholder_text=sugerencia_texto)
        if tipo_validacion:
            campo_entrada.configure(validate="key", validatecommand=(tipo_validacion, "%P"))
        campo_entrada.grid(row=fila+1, column=columna, sticky="w", padx=25, pady=(0, 8))
        return campo_entrada

    #validadores en tiempo real : filtran todos los campos o input para crear empleados
    entrada_cedula = crear_campo("Cédula:", 0, 0, validacion_cedula, "5-10 dígitos (Solo números)")
    entrada_nombre = crear_campo("Nombres:", 2, 0, validacion_letras, "2-20 letras")
    entrada_apellido = crear_campo("Apellidos:", 2, 1, validacion_letras, "2-20 letras")
    entrada_telefono = crear_campo("Teléfono:", 0, 1, validacion_telefono, "11 dígitos")
    entrada_correo = crear_campo("Correo Electrónico:", 4, 0, validacion_correo, "14-50 caracteres (Requiere @)")
    entrada_cargo = crear_campo("Cargo:", 4, 1, validacion_letras, "3-15 letras")
    entrada_fecha_nacimiento = crear_campo("Fecha de Nacimiento:", 6, 0, validacion_fecha, "DD/MM/AAAA")
    entrada_fecha_ingreso = crear_campo("Fecha de Ingreso:", 6, 1, validacion_fecha, "DD/MM/AAAA")
    entrada_sueldo = crear_campo("Sueldo Base (Bs.):", 8, 0, validacion_sueldo, "Ej: 999999,9999")
    entrada_direccion = crear_campo("Dirección de Habitación:", 8, 1, validacion_direccion, "5-50 caracteres (Letras y números)")

    lista_campos = [
        entrada_cedula, entrada_nombre, entrada_apellido, entrada_telefono, entrada_correo, 
        entrada_cargo, entrada_fecha_nacimiento, entrada_fecha_ingreso, entrada_sueldo, entrada_direccion
    ]

    
    marco_botones = ctk.CTkFrame(ventana_registro_formulario, fg_color="transparent")
    marco_botones.pack(pady=25)

    #boton para guardar empleados
    boton_guardar = ctk.CTkButton(
        marco_botones, text="Guardar Registro", width=220, height=45, 
        font=("Arial", 16, "bold"), fg_color="#2fa572", hover_color="#2a394a",
        command=lambda: guardar_empleado(lista_campos, ventana_registro_formulario, callback_actualizar)
    )
    boton_guardar.grid(row=0, column=0, padx=12)
    
    #boton para cancelar el guardadop de empleados
    boton_cancelar = ctk.CTkButton(
        marco_botones, text="Cancelar", width=220, height=45, 
        font=("Arial", 16, "bold"), fg_color="#ce1b1b", hover_color="#2a394a",
        command=ventana_registro_formulario.destroy
    )
    boton_cancelar.grid(row=0, column=1, padx=12)