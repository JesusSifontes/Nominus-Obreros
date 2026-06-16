import customtkinter as ctk
from tkinter import messagebox, ttk
from database import conectar
from datetime import datetime
import os
from decimal import Decimal, ROUND_HALF_UP

def convertir_a_decimal(valor_origen):
    """Convierte cualquier valor a Decimal de forma segura."""
    if valor_origen is None:
        return Decimal('0.0000')
    return Decimal(str(valor_origen))

def redondear_financiero(valor_decimal):
    """Redondea de forma financiera a 4 decimales exactos."""
    return valor_decimal.quantize(Decimal('0.0000'), rounding=ROUND_HALF_UP)

def formatear_moneda(valor_numerico):
    """Convierte un Decimal o float al formato de moneda local: 58.000,0123"""
    valor_decimal = convertir_a_decimal(valor_numerico)
    parte_entera, parte_decimal = f"{valor_decimal:.4f}".split('.')
    entera_con_puntos = f"{int(parte_entera):,}".replace(',', '.')
    return f"{entera_con_puntos},{parte_decimal}"

def obtener_reglas_ley():
    diccionario_reglas = {}
    try:
        conexion_base_datos = conectar()
        cursor_base_datos = conexion_base_datos.cursor()
        cursor_base_datos.execute("SELECT nombre_regla, porcentaje FROM ley_nomina")
        for nombre_regla, valor_porcentaje in cursor_base_datos.fetchall():
            diccionario_reglas[nombre_regla] = convertir_a_decimal(valor_porcentaje)
        conexion_base_datos.close()
    except Exception as error_reglas:
        print(f"Error al obtener reglas: {error_reglas}")
    
    if 'SSO' not in diccionario_reglas: diccionario_reglas['SSO'] = convertir_a_decimal(0.04)
    if 'FAOV' not in diccionario_reglas: diccionario_reglas['FAOV'] = convertir_a_decimal(0.01)
    if 'PI' not in diccionario_reglas: diccionario_reglas['PI'] = convertir_a_decimal(0.005)
    if 'CESTA TICKET' not in diccionario_reglas: diccionario_reglas['CESTA TICKET'] = convertir_a_decimal(0)
    if 'BONO DE GUERRA ECONOMICA' not in diccionario_reglas: diccionario_reglas['BONO DE GUERRA ECONOMICA'] = convertir_a_decimal(0)
    return diccionario_reglas

def validar_novedades(texto_ingresado, tipo_campo):
    """Valida en tiempo real que solo entren números enteros y respete los máximos."""
    if texto_ingresado == "": return True
    if not texto_ingresado.isdigit(): return False
    
    valor_numerico = int(texto_ingresado)
    if tipo_campo == "horas":
        return 0 <= valor_numerico <= 20
    if tipo_campo == "ausencias":
        return 0 <= valor_numerico <= 15
    return True

def calcular_nomina_empleado(sueldo_mensual, diccionario_reglas, cantidad_horas_extra=0, dias_ausencia=0):
    sueldo_mensual_decimal = convertir_a_decimal(sueldo_mensual)
    horas_extra_decimal = convertir_a_decimal(cantidad_horas_extra)
    dias_ausencia_decimal = convertir_a_decimal(dias_ausencia)
    
    sueldo_quincenal = sueldo_mensual_decimal / convertir_a_decimal(2)
    
    sueldo_diario = sueldo_mensual_decimal / convertir_a_decimal(30)
    hora_ordinaria = sueldo_diario / convertir_a_decimal(8)
    valor_hora_extra = hora_ordinaria * convertir_a_decimal(1.5)
    monto_total_horas_extra = horas_extra_decimal * valor_hora_extra
    monto_descuento_ausencias = dias_ausencia_decimal * sueldo_diario
    
    factor_semanal = (sueldo_mensual_decimal * convertir_a_decimal(12)) / convertir_a_decimal(52)
    seguro_social_sso = factor_semanal * diccionario_reglas.get('SSO', convertir_a_decimal(0.04)) * convertir_a_decimal(2)
    politica_habitacional_faov = factor_semanal * diccionario_reglas.get('FAOV', convertir_a_decimal(0.01)) * convertir_a_decimal(2)
    paro_forzoso_pi = factor_semanal * diccionario_reglas.get('PI', convertir_a_decimal(0.005)) * convertir_a_decimal(2)
    monto_total_deducciones = seguro_social_sso + politica_habitacional_faov + paro_forzoso_pi
    
    bono_guerra_quincenal = diccionario_reglas.get('BONO DE GUERRA ECONOMICA', convertir_a_decimal(0)) / convertir_a_decimal(2)
    cesta_ticket_quincenal = diccionario_reglas.get('CESTA TICKET', convertir_a_decimal(0)) / convertir_a_decimal(2)
    monto_total_asignaciones = bono_guerra_quincenal + cesta_ticket_quincenal + monto_total_horas_extra
    
    neto_a_cobrar = (sueldo_quincenal - monto_descuento_ausencias - monto_total_deducciones) + (bono_guerra_quincenal + cesta_ticket_quincenal)
    if neto_a_cobrar < 0: neto_a_cobrar = convertir_a_decimal(0)
    
    return {
        "sueldo_quincenal": redondear_financiero(sueldo_quincenal),
        "horas_extra_monto": redondear_financiero(monto_total_horas_extra),
        "ausencias_monto": redondear_financiero(monto_descuento_ausencias),
        "sso": redondear_financiero(seguro_social_sso), 
        "faov": redondear_financiero(politica_habitacional_faov), 
        "pi": redondear_financiero(paro_forzoso_pi), 
        "total_deducciones": redondear_financiero(monto_total_deducciones),
        "bono_guerra": redondear_financiero(bono_guerra_quincenal), 
        "cesta_ticket": redondear_financiero(cesta_ticket_quincenal), 
        "total_asignaciones": redondear_financiero(monto_total_asignaciones), 
        "neto": redondear_financiero(neto_a_cobrar)
    }

def procesar_y_finalizar(lista_empleados_nomina, ventana):
    fecha_actual_sistema = datetime.now().strftime("%d-%m-%Y")
    carpeta_destino_recibos = "recibos_nomina"
    
    if not os.path.exists(carpeta_destino_recibos):
        os.makedirs(carpeta_destino_recibos)

    try:
        for empleado_datos in lista_empleados_nomina:
            nombre_limpio_archivo = f"{empleado_datos['nombre']}_{empleado_datos['cargo']}".replace(" ", "_")
            nombre_archivo_txt = f"{empleado_datos['cedula']}-{nombre_limpio_archivo}-{fecha_actual_sistema}.txt"
            ruta_completa_archivo = os.path.join(carpeta_destino_recibos, nombre_archivo_txt)
            
            with open(ruta_completa_archivo, "w", encoding="utf-8") as archivo_recibo:
                archivo_recibo.write(f"RECIBO DE PAGO QUINCENAL: {empleado_datos['nombre']}\n")
                archivo_recibo.write(f"ID: {empleado_datos['id']} | CEDULA: {empleado_datos['cedula']} | CARGO: {empleado_datos['cargo']}\n")
                archivo_recibo.write("-" * 65 + "\n")
                archivo_recibo.write(f"SUELDO QUINCENAL (Base/2):           {formatear_moneda(empleado_datos['sueldo_q'])} Bs\n")
                archivo_recibo.write(f"ASIGNACION HORAS EXTRA:              {formatear_moneda(empleado_datos['he_monto'])} Bs ({int(empleado_datos['he_cant'])} Horas)\n")
                archivo_recibo.write(f"CESTA TICKET (Quincenal):            {formatear_moneda(empleado_datos['cesta'])} Bs\n")
                archivo_recibo.write(f"BONO GUERRA ECONÓMICA (Quincenal):   {formatear_moneda(empleado_datos['guerra'])} Bs\n")
                archivo_recibo.write(f"(+) TOTAL ASIGNACIONES:              {formatear_moneda(empleado_datos['t_asig'])} Bs\n")
                archivo_recibo.write("-" * 65 + "\n")
                archivo_recibo.write(f"DEDUCCIÓN POR AUSENCIAS:             {formatear_moneda(empleado_datos['aus_monto'])} Bs ({int(empleado_datos['aus_dias'])} Días)\n")
                archivo_recibo.write(f"RETENCIÓN SEGURO SOCIAL (SSO):       {formatear_moneda(empleado_datos['sso'])} Bs\n")
                archivo_recibo.write(f"RETENCIÓN VIVIENDA (FAOV):           {formatear_moneda(empleado_datos['faov'])} Bs\n")
                archivo_recibo.write(f"RETENCIÓN PARO FORZOSO (PI):         {formatear_moneda(empleado_datos['pi'])} Bs\n")
                archivo_recibo.write(f"(-) TOTAL DEDUCCIONES:               {formatear_moneda(empleado_datos['t_deduc'])} Bs\n")
                archivo_recibo.write("=" * 65 + "\n")
                archivo_recibo.write(f"NETO A COBRAR QUINCENA:              {formatear_moneda(empleado_datos['neto'])} Bs\n")
        
        ventana.destroy()
        messagebox.showinfo("Nómina Procesada", f"Nómina quincenal finalizada con éxito.\nSe generaron {len(lista_empleados_nomina)} recibos en la carpeta '{carpeta_destino_recibos}'.")
        
    except Exception as error_proceso:
        messagebox.showerror("Error", f"No se pudo completar el proceso: {error_proceso}")

def ventana_nomina():
    ventana_modulo_nomina = ctk.CTkToplevel()
    ventana_modulo_nomina.title("Módulo de Nómina Quincenal - Personal Obrero")
    ventana_modulo_nomina.geometry("1500x730") 
    ventana_modulo_nomina.grab_set()

    diccionario_reglas_ley = obtener_reglas_ley()
    datos_internos_nomina = []

    validacion_horas_extra = ventana_modulo_nomina.register(lambda P: validar_novedades(P, "horas"))
    validacion_ausencias = ventana_modulo_nomina.register(lambda P: validar_novedades(P, "ausencias"))

    marco_control_superior = ctk.CTkFrame(ventana_modulo_nomina)
    marco_control_superior.pack(fill="x", padx=20, pady=10)

    ctk.CTkLabel(marco_control_superior, text="Panel de Carga (Seleccione un obrero en la tabla):", font=("Arial", 13, "bold")).grid(row=0, column=0, columnspan=5, padx=10, pady=5, sticky="w")
    
    ctk.CTkLabel(marco_control_superior, text="Horas Extra (Máx 20):").grid(row=1, column=0, padx=10, pady=5)
    cuadro_entrada_horas_extra = ctk.CTkEntry(marco_control_superior, width=110, placeholder_text="0-20", validate="key", validatecommand=(validacion_horas_extra, "%P"))
    cuadro_entrada_horas_extra.grid(row=1, column=1, padx=10, pady=5)
    cuadro_entrada_horas_extra.insert(0, "0")

    ctk.CTkLabel(marco_control_superior, text="Días de Ausencia (Máx 15):").grid(row=1, column=2, padx=10, pady=5)
    cuadro_entrada_ausencias = ctk.CTkEntry(marco_control_superior, width=110, placeholder_text="0-15", validate="key", validatecommand=(validacion_ausencias, "%P"))
    cuadro_entrada_ausencias.grid(row=1, column=3, padx=10, pady=5)
    cuadro_entrada_ausencias.insert(0, "0")

    marco_tabla_datos = ctk.CTkFrame(ventana_modulo_nomina)
    marco_tabla_datos.pack(fill="both", expand=True, padx=20, pady=5)

    titulos_columnas = (
        "Id", "Cédula", "Nombre", "Cargo", "Sueldo Base M.", "Sueldo Quinc.",
        "H. Extra Cant", "H. Extra Bs.", "Ausencias Bs.", "Cesta T.", 
        "B. Guerra", "T. Asig", "SSO", "FAOV", "PI", "T. Deduc", "Neto a Pagar"
    )
    
    tabla_visual_treeview = ttk.Treeview(marco_tabla_datos, columns=titulos_columnas, show='headings')
    
    for nombre_columna in titulos_columnas:
        tabla_visual_treeview.heading(nombre_columna, text=nombre_columna)
        if nombre_columna in ["Id", "Cédula", "H. Extra Cant"]:
            tabla_visual_treeview.column(nombre_columna, width=75, anchor="center")
        elif nombre_columna in ["Nombre", "Cargo"]:
            tabla_visual_treeview.column(nombre_columna, width=140, anchor="w")
        else:
            tabla_visual_treeview.column(nombre_columna, width=100, anchor="e")
    
    barra_desplazamiento_vertical = ttk.Scrollbar(marco_tabla_datos, orient="vertical", command=tabla_visual_treeview.yview)
    barra_desplazamiento_horizontal = ttk.Scrollbar(marco_tabla_datos, orient="horizontal", command=tabla_visual_treeview.xview)
    tabla_visual_treeview.configure(yscrollcommand=barra_desplazamiento_vertical.set, xscrollcommand=barra_desplazamiento_horizontal.set)
    barra_desplazamiento_vertical.pack(side="right", fill="y")
    barra_desplazamiento_horizontal.pack(side="bottom", fill="x")
    tabla_visual_treeview.pack(fill="both", expand=True)

    etiqueta_costo_total = ctk.CTkLabel(ventana_modulo_nomina, text="Costo total de la Quincena: 0,0000 Bs", font=("Arial", 18, "bold"), text_color="#2fa572")

    def recalcular_todo():
        nonlocal datos_internos_nomina
        datos_internos_nomina.clear()
        for elemento_id in tabla_visual_treeview.get_children():
            tabla_visual_treeview.delete(elemento_id)
            
        monto_total_general = Decimal('0.0000')
        
        try:
            conexion_base_datos = conectar()
            cursor_base_datos = conexion_base_datos.cursor()
            cursor_base_datos.execute("SELECT id, cedula, nombre, apellido, sueldo_base, cargo FROM empleados")
            lista_obreros = cursor_base_datos.fetchall()
            conexion_base_datos.close()
            
            for obrero in lista_obreros:
                id_empleado, cedula, nombre, apellido, sueldo_base_mensual, cargo = obrero
                nombre_completo = f"{nombre.title()} {apellido.title()}"
                
                calculos_empleado = calcular_nomina_empleado(sueldo_base_mensual, diccionario_reglas_ley, 0, 0)
                monto_total_general += calculos_empleado['neto']
                
                datos_internos_nomina.append({
                    "id": id_empleado, "cedula": cedula, "nombre": nombre_completo, "cargo": cargo.title(),
                    "sueldo_m": convertir_a_decimal(sueldo_base_mensual), "sueldo_q": calculos_empleado['sueldo_quincenal'],
                    "he_cant": Decimal('0'), "he_monto": calculos_empleado['horas_extra_monto'],
                    "aus_dias": Decimal('0'), "aus_monto": calculos_empleado['ausencias_monto'],
                    "cesta": calculos_empleado['cesta_ticket'], "guerra": calculos_empleado['bono_guerra'],
                    "t_asig": calculos_empleado['total_asignaciones'], "sso": calculos_empleado['sso'], "faov": calculos_empleado['faov'],
                    "pi": calculos_empleado['pi'], "t_deduc": calculos_empleado['total_deducciones'], "neto": calculos_empleado['neto']
                })
                
                tabla_visual_treeview.insert("", "end", iid=str(id_empleado), values=(
                    id_empleado, cedula, nombre_completo, cargo.title(), formatear_moneda(sueldo_base_mensual), formatear_moneda(calculos_empleado['sueldo_quincenal']),
                    "0", formatear_moneda(calculos_empleado['horas_extra_monto']), formatear_moneda(calculos_empleado['ausencias_monto']),
                    formatear_moneda(calculos_empleado['cesta_ticket']), formatear_moneda(calculos_empleado['bono_guerra']), formatear_moneda(calculos_empleado['total_asignaciones']),
                    formatear_moneda(calculos_empleado['sso']), formatear_moneda(calculos_empleado['faov']), formatear_moneda(calculos_empleado['pi']), 
                    formatear_moneda(calculos_empleado['total_deducciones']), formatear_moneda(calculos_empleado['neto'])
                ))
                
            etiqueta_costo_total.configure(text=f"Costo total de la Quincena: {formatear_moneda(monto_total_general)} Bs")
        except Exception as error_recalculo:
            messagebox.showerror("Error", f"Fallo al procesar datos de nómina: {error_recalculo}")

    def aplicar_novedad():
        seleccion_elemento = tabla_visual_treeview.selection()
        if not seleccion_elemento:
            messagebox.showwarning("Atención", "Por favor, seleccione un obrero de la lista para aplicarle las novedades.")
            return
        
        cantidad_he_ingresada = int(cuadro_entrada_horas_extra.get()) if cuadro_entrada_horas_extra.get() else 0
        cantidad_aus_ingresada = int(cuadro_entrada_ausencias.get()) if cuadro_entrada_ausencias.get() else 0

        if not (0 <= cantidad_he_ingresada <= 20) or not (0 <= cantidad_aus_ingresada <= 15):
            messagebox.showerror("Error", "Los valores exceden el rango permitido (0-20 Horas / 0-15 Días).")
            return

        empleado_id_seleccionado = int(seleccion_elemento[0])
        
        for empleado_registro in datos_internos_nomina:
            if empleado_registro['id'] == empleado_id_seleccionado:
                calculos_nuevos = calcular_nomina_empleado(empleado_registro['sueldo_m'], diccionario_reglas_ley, cantidad_he_ingresada, cantidad_aus_ingresada)
                
                empleado_registro['he_cant'] = convertir_a_decimal(cantidad_he_ingresada)
                empleado_registro['he_monto'] = calculos_nuevos['horas_extra_monto']
                empleado_registro['aus_dias'] = convertir_a_decimal(cantidad_aus_ingresada)
                empleado_registro['aus_monto'] = calculos_nuevos['ausencias_monto']
                empleado_registro['t_asig'] = calculos_nuevos['total_asignaciones']
                empleado_registro['sso'] = calculos_nuevos['sso']
                empleado_registro['faov'] = calculos_nuevos['faov']
                empleado_registro['pi'] = calculos_nuevos['pi']
                empleado_registro['t_deduc'] = calculos_nuevos['total_deducciones']
                empleado_registro['neto'] = calculos_nuevos['neto']
                
                tabla_visual_treeview.item(str(empleado_id_seleccionado), values=(
                    empleado_registro['id'], empleado_registro['cedula'], empleado_registro['nombre'], empleado_registro['cargo'], formatear_moneda(empleado_registro['sueldo_m']), formatear_moneda(empleado_registro['sueldo_q']),
                    cantidad_he_ingresada, formatear_moneda(empleado_registro['he_monto']), formatear_moneda(empleado_registro['aus_monto']),
                    formatear_moneda(empleado_registro['cesta']), formatear_moneda(empleado_registro['guerra']), formatear_moneda(empleado_registro['t_asig']),
                    formatear_moneda(empleado_registro['sso']), formatear_moneda(empleado_registro['faov']), formatear_moneda(empleado_registro['pi']), 
                    formatear_moneda(empleado_registro['t_deduc']), formatear_moneda(empleado_registro['neto'])
                ))
                break
                
        monto_total_actualizado = sum(empleado_registro['neto'] for empleado_registro in datos_internos_nomina)
        etiqueta_costo_total.configure(text=f"Costo total de la Quincena: {formatear_moneda(monto_total_actualizado)} Bs")

    boton_aplicar_novedades = ctk.CTkButton(
        marco_control_superior, text="Aplicar Novedades", 
        fg_color="#2f6ba5", hover_color="#2a394a", 
        font=("Arial", 12, "bold"), command=aplicar_novedad
    )
    boton_aplicar_novedades.grid(row=1, column=4, padx=15, pady=5)

    recalcular_todo()
    etiqueta_costo_total.pack(pady=5)

    boton_procesar_nomina = ctk.CTkButton(
        ventana_modulo_nomina, text="Procesar Pagos y Generar Recibos de Nómina", 
        fg_color="#2fa572", hover_color="#2a394a",
        width=380, height=50, font=("Arial", 16, "bold"),
        command=lambda: procesar_y_finalizar(datos_internos_nomina, ventana_modulo_nomina)
    )
    boton_procesar_nomina.pack(pady=15)