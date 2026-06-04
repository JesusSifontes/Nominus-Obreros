import customtkinter as ctk
from tkinter import messagebox
import re
from database import conectar

def validar_inputs(texto_ingresado, tipo_validacion):
    if texto_ingresado == "": return True
    
    if tipo_validacion == "cedula":
        if len(texto_ingresado) > 10: return False
        return texto_ingresado.isdigit()
        
    if tipo_validacion == "letras":
        if len(texto_ingresado) > 20: return False
        return all(caracter.isalpha() or caracter.isspace() for caracter in texto_ingresado)  
    
    if tipo_validacion == "correo":
        return len(texto_ingresado) <= 50

    if tipo_validacion == "direccion":
        if len(texto_ingresado) > 50: return False
        return all(caracter.isalnum() or caracter.isspace() for caracter in texto_ingresado)
    
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
    
    if tipo_validacion == "fecha":
        if len(texto_ingresado) > 10: return False
        return all(caracter.isdigit() or caracter == '/' for caracter in texto_ingresado)
    
    if tipo_validacion == "numeros":
        if len(texto_ingresado) > 11: return False
        return texto_ingresado.isdigit()

    return True


def actualizar_empleado(id_empleado, lista_campos_entradas, ventana, callback_actualizar):
    
    valores_extraidos = [campo.get().strip() for campo in lista_campos_entradas]
    
    (cedula, nombre, apellido, telefono, correo, cargo, 
     fecha_nacimiento, fecha_ingreso, sueldo_texto, direccion) = valores_extraidos

    if not all(valores_extraidos):
        messagebox.showwarning("Error", "Todos los campos son obligatorios.")
        return

    if not (5 <= len(cedula) <= 10):
        messagebox.showwarning("Error", "Cédula: debe tener entre 5 and 10 dígitos numéricos (sin puntos ni comas).")
        return

    if len(telefono) != 11:
        messagebox.showwarning("Error", "Teléfono: debe tener exactamente 11 caracteres.")
        return

    if not (2 <= len(nombre) <= 20) or not (2 <= len(apellido) <= 20):
        messagebox.showwarning("Error", "Nombres y Apellidos: deben tener entre 2 and 20 caracteres (solo letras).")
        return

    if not (14 <= len(correo) <= 50) or "@" not in correo:
        messagebox.showwarning("Error", "Correo Electrónico: debe tener entre 14 and 50 caracteres y contener un '@' válido.")
        return

    if not (3 <= len(cargo) <= 15):
        messagebox.showwarning("Error", "Cargo: debe tener entre 3 and 15 letras.")
        return

    if not (5 <= len(direccion) <= 50):
        messagebox.showwarning("Error", "Dirección: debe tener entre 5 and 50 caracteres.")
        return

    formato_fecha = r"^\d{2}/\d{2}/\d{4}$"
    if not re.match(formato_fecha, fecha_nacimiento) or not re.match(formato_fecha, fecha_ingreso):
        messagebox.showwarning("Error", "Fechas: deben cumplir el formato DD/MM/AAAA.")
        return


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
            UPDATE empleados SET 
                cedula = ?, nombre = ?, apellido = ?, telefono = ?, correo = ?, 
                cargo = ?, fecha_nacimiento = ?, fecha_ingreso = ?, sueldo_base = ?, direccion = ?
            WHERE id = ?
        """, (cedula, nombre.lower(), apellido.lower(), telefono, correo.lower(), cargo.lower(), 
              fecha_nacimiento, fecha_ingreso, round(sueldo_decimal, 4), direccion, id_empleado))
        
        conexion_base_datos.commit()
        conexion_base_datos.close()
        
        messagebox.showinfo("Éxito", f"Datos de {nombre.upper()} actualizados correctamente.")
        ventana.destroy() 
        
        if callback_actualizar:
            callback_actualizar() 

    except Exception as error:
        messagebox.showerror("Error", f"Error al actualizar: {error}")


def ventana_editar(datos_actuales, callback_actualizar=None):
    
    id_empleado = datos_actuales[0]
    
    ventana_editar_formulario = ctk.CTkToplevel()
    ventana_editar_formulario.title("Editar Empleado - Nominus-Obreros")
    ventana_editar_formulario.geometry("900x580") 
    ventana_editar_formulario.resizable(False, False)
    ventana_editar_formulario.grab_set()


    validacion_cedula = ventana_editar_formulario.register(lambda P: validar_inputs(P, "cedula"))
    validacion_letras = ventana_editar_formulario.register(lambda P: validar_inputs(P, "letras"))
    validacion_correo = ventana_editar_formulario.register(lambda P: validar_inputs(P, "correo"))
    validacion_direccion = ventana_editar_formulario.register(lambda P: validar_inputs(P, "direccion"))
    validacion_telefono = ventana_editar_formulario.register(lambda P: validar_inputs(P, "numeros")) 
    validacion_sueldo = ventana_editar_formulario.register(lambda P: validar_inputs(P, "sueldo"))
    validacion_fecha = ventana_editar_formulario.register(lambda P: validar_inputs(P, "fecha"))

    ctk.CTkLabel(ventana_editar_formulario, text="Modificar Información del Empleado", font=("Arial", 18, "bold")).pack(pady=(20, 10))

    marco_formulario = ctk.CTkFrame(ventana_editar_formulario, fg_color="transparent")
    marco_formulario.pack(fill="x", padx=30) 
    marco_formulario.grid_columnconfigure(0, weight=1)
    marco_formulario.grid_columnconfigure(1, weight=1)

    def crear_campo(etiqueta_texto, fila, columna, tipo_validacion, texto_inicial):
        etiqueta = ctk.CTkLabel(marco_formulario, text=etiqueta_texto, font=("Arial", 12, "bold"))
        etiqueta.grid(row=fila, column=columna, sticky="w", padx=25, pady=(8, 0))
        campo_entrada = ctk.CTkEntry(marco_formulario, width=380, height=35)
        if tipo_validacion:
            campo_entrada.configure(validate="key", validatecommand=(tipo_validacion, "%P"))
        campo_entrada.insert(0, str(texto_inicial)) 
        campo_entrada.grid(row=fila+1, column=columna, sticky="w", padx=25, pady=(0, 8))
        return campo_entrada


    sueldo_inicial_con_coma = f"{datos_actuales[9]:.4f}".replace(".", ",")


    entrada_cedula = crear_campo("Cédula:", 0, 0, validacion_cedula, datos_actuales[1])
    entrada_nombre = crear_campo("Nombres:", 2, 0, validacion_letras, datos_actuales[2].title())
    entrada_apellido = crear_campo("Apellidos:", 2, 1, validacion_letras, datos_actuales[3].title())
    entrada_telefono = crear_campo("Teléfono:", 0, 1, validacion_telefono, datos_actuales[4])
    entrada_correo = crear_campo("Correo Electrónico:", 4, 0, validacion_correo, datos_actuales[5])
    entrada_cargo = crear_campo("Cargo:", 4, 1, validacion_letras, datos_actuales[8].title())
    entrada_fecha_nacimiento = crear_campo("Fecha de Nacimiento:", 6, 0, validacion_fecha, datos_actuales[10])
    entrada_fecha_ingreso = crear_campo("Fecha de Ingreso:", 6, 1, validacion_fecha, datos_actuales[7])
    entrada_sueldo = crear_campo("Sueldo Base (Bs.):", 8, 0, validacion_sueldo, sueldo_inicial_con_coma)
    entrada_direccion = crear_campo("Dirección de Habitación:", 8, 1, validacion_direccion, datos_actuales[6])

    lista_campos = [
        entrada_cedula, entrada_nombre, entrada_apellido, entrada_telefono, entrada_correo, 
        entrada_cargo, entrada_fecha_nacimiento, entrada_fecha_ingreso, entrada_sueldo, entrada_direccion
    ]

    marco_botones = ctk.CTkFrame(ventana_editar_formulario, fg_color="transparent")
    marco_botones.pack(pady=25)


    ctk.CTkButton(
        marco_botones, text="Actualizar Datos", width=220, height=45, 
        font=("Arial", 16, "bold"), fg_color="#2f6ba5", hover_color="#2a394a",
        command=lambda: actualizar_empleado(id_empleado, lista_campos, ventana_editar_formulario, callback_actualizar)
    ).grid(row=0, column=0, padx=12)
    

    ctk.CTkButton(
        marco_botones, text="Cancelar", width=220, height=45, 
        font=("Arial", 16, "bold"), fg_color="#a52f2f", hover_color="#2a394a",
        command=ventana_editar_formulario.destroy
    ).grid(row=0, column=1, padx=12)