import streamlit as st
import pandas as pd
import os
from datetime import datetime
import time
import uuid
import re

# Configuración de la página
st.set_page_config(page_title="Visión de Futuro", layout="wide")

# Rutas de las bases de datos separadas (Diseño relacional por seguridad)
ARCHIVO_SENSIBLE = "datos_sensibles.csv"
ARCHIVO_ESTADISTICO = "estadisticas_anonimas.csv"
ARCHIVO_TELEMETRIA = "telemetria.csv"

# --- 1. MANEJO DE SESIÓN E INICIALIZACIÓN ---
if "conectado" not in st.session_state:
    st.session_state.conectado = False
if "rol" not in st.session_state:
    st.session_state.rol = None
if "form_key" not in st.session_state:
    st.session_state.form_key = 1
# Variable para manejar la pantalla de selección de los botones grandes
if "perfil_seleccionado" not in st.session_state:
    st.session_state.perfil_seleccionado = None

# Variables para la Telemetría
if "tiempo_inicio" not in st.session_state:
    st.session_state.tiempo_inicio = time.time()
if "errores_carga" not in st.session_state:
    st.session_state.errores_carga = 0

# --- 2. CARTEL EMERGENTE (MODAL) ---
@st.dialog("✅ Carga Exitosa")
def mostrar_cartel_resultado(estado_triaje, agudeza):
    st.write("Los datos del alumno han sido guardados correctamente de forma segura y disociada.")
    
    if "Sospechoso" in estado_triaje:
        st.error(f"{estado_triaje} (Agudeza mínima detectada: {agudeza}/10)")
    else:
        st.success(f"{estado_triaje} (Agudeza mínima detectada: {agudeza}/10)")
        
    if st.button("OK - Cargar nuevo alumno", type="primary", use_container_width=True):
        st.rerun()

# --- 3. PANTALLAS DE INICIO DE SESIÓN ---
if not st.session_state.conectado:
    
    # 3.A: Pantalla principal de selección de perfil
    if st.session_state.perfil_seleccionado is None:
        st.write("")
        st.markdown("<h1 style='text-align: center;'>Plataforma Visión de Futuro</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray; font-size: 18px;'>Sistema de Tamizaje Visual y Derivación Segura</p>", unsafe_allow_html=True)
        st.write("")
        st.write("")
        
        # Columnas (Perfil Escolar - Escudo - Perfil Médico)
        col_doc, col_escudo, col_med = st.columns([2, 1, 2])
        
        with col_doc:
            st.info("👩‍🏫 **PERFIL ESCOLAR AUTORIZADO**")
            if st.button("Ingresar como Docente", use_container_width=True):
                st.session_state.perfil_seleccionado = "Docente"
                st.rerun()
                
        with col_escudo:
            st.markdown("<h1 style='text-align: center; font-size: 60px;'>🛡️</h1>", unsafe_allow_html=True)
            
        with col_med:
            st.success("👨‍⚕️ **PERFIL MÉDICO AUTORIZADO**")
            if st.button("Ingresar como Personal CIC", use_container_width=True):
                st.session_state.perfil_seleccionado = "Personal del CIC"
                st.rerun()
                
    # 3.B: Pantalla de ingreso de contraseña
    else:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title(f"🔐 Acceso: {st.session_state.perfil_seleccionado}")
            
            # Solo pedimos la contraseña
            contrasena = st.text_input("Ingrese su contraseña:", type="password")
            
            # Botones en paralelo para Volver o Iniciar Sesión
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1:
                if st.button("⬅️ Volver a los perfiles", use_container_width=True):
                    st.session_state.perfil_seleccionado = None
                    st.rerun()
            with col_btn2:
                if st.button("Iniciar Sesión", type="primary", use_container_width=True):
                    # Validamos únicamente la contraseña según el perfil seleccionado
                    if st.session_state.perfil_seleccionado == "Docente" and contrasena == "1234":
                        st.session_state.conectado = True
                        st.session_state.rol = "Docente"
                        st.session_state.tiempo_inicio = time.time() # Inicia el reloj al entrar
                        st.rerun()
                    elif st.session_state.perfil_seleccionado == "Personal del CIC" and contrasena == "admin":
                        st.session_state.conectado = True
                        st.session_state.rol = "CIC"
                        st.rerun()
                    else:
                        st.error("⚠️ Contraseña incorrecta. Verifique sus datos.")
            
            st.divider()
            
            # --- LÓGICA DEL CARTEL DINÁMICO ---
            if st.session_state.perfil_seleccionado == "Docente":
                st.info("💡 **Datos de acceso:**\n- Clave autorizada: `1234`")
            elif st.session_state.perfil_seleccionado == "Personal del CIC":
                st.info("💡 **Datos de acceso:**\n- Clave autorizada: `admin`")

# --- 4. SISTEMA PRINCIPAL ---
else:
    st.sidebar.title("Opciones")
    st.sidebar.success(f"👤 Conectado como: **{st.session_state.rol}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.conectado = False
        st.session_state.rol = None
        st.session_state.perfil_seleccionado = None # Resetea la selección al salir
        st.rerun()

    # -----------------------------------------
    # VISTA DOCENTE
    # -----------------------------------------
    if st.session_state.rol == "Docente":
        st.title("📝 Planilla de Tamizaje Visual")
        st.write("Complete los datos extraídos de la planilla física.")

        with st.form(f"formulario_completo_{st.session_state.form_key}"):
            st.subheader("Datos Personales")
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre:")
                dni = st.text_input("DNI:")
                fecha_nac = st.date_input("Fecha de Nac:", format="DD/MM/YYYY")
                escuela = st.text_input("Institución Escolar:")
            with col2:
                apellido = st.text_input("Apellido:")
                edad = st.number_input("Edad:", min_value=5, max_value=12, value=6, step=1)
                direccion = st.text_input("Dirección:")

            st.subheader("Agudeza Visual")
            st.info("Ingrese valores del 1 al 10. Si no usa corrección, deje los campos 'Con Corrección' en 0.")
            
            col_sc, col_cc = st.columns(2)
            with col_sc:
                st.markdown("**Sin Corrección**")
                col_sc1, col_sc2 = st.columns(2)
                with col_sc1:
                    od_sc = st.number_input("OD (Sin Correc.):", min_value=1, max_value=10, value=10)
                with col_sc2:
                    oi_sc = st.number_input("OI (Sin Correc.):", min_value=1, max_value=10, value=10)
            
            with col_cc:
                st.markdown("**Con Corrección (Lentes)**")
                col_cc1, col_cc2 = st.columns(2)
                with col_cc1:
                    od_cc = st.number_input("OD (Con Correc.):", min_value=0, max_value=10, value=0)
                with col_cc2:
                    oi_cc = st.number_input("OI (Con Correc.):", min_value=0, max_value=10, value=0)

            st.subheader("Antecedentes y Tratamiento")
            col_ant1, col_ant2, col_ant3 = st.columns(3)
            with col_ant1:
                consulta_previa = st.radio("Consultó Anteriormente con un Oftalmólogo:", ["SI", "NO"], index=1)
            with col_ant2:
                usa_anteojos = st.radio("Usa Anteojos:", ["SI", "NO"], index=1)
            with col_ant3:
                otro_tratamiento = st.radio("Recibe algún otro tratamiento Oftalmológico:", ["SI", "NO"], index=1)

            observaciones = st.text_area("Observaciones:")

            enviado = st.form_submit_button("Guardar y Evaluar")

            if enviado:
            # Patrones de validación
                patron_nombre = r'^[A-Za-zÁÉÍÓÚáéíóúÑñÜü\s]+$'   # solo letras y espacios
                patron_dni = r'^\d+$'                              # solo números

                campos_vacios = nombre == "" or apellido == "" or dni == "" or escuela == ""
                nombre_invalido = not campos_vacios and not re.match(patron_nombre, nombre)
                apellido_invalido = not campos_vacios and not re.match(patron_nombre, apellido)
                dni_invalido = not campos_vacios and not re.match(patron_dni, dni)

                if campos_vacios:
                    st.warning("⚠️ Por favor, complete al menos Nombre, Apellido, DNI e Institución Escolar.")
                    st.session_state.errores_carga += 1
                elif nombre_invalido or apellido_invalido:
                    st.warning("⚠️ Nombre y Apellido solo pueden contener letras.")
                    st.session_state.errores_carga += 1
                elif dni_invalido:
                    st.warning("⚠️ El DNI solo puede contener números.")
                    st.session_state.errores_carga += 1
                else:
                # --- VALIDACIÓN: BLOQUEO DE DUPLICADOS CON DERIVACIÓN ---
                    carga_permitida = True
                    if os.path.isfile(ARCHIVO_SENSIBLE):
                        df_existente = pd.read_csv(ARCHIVO_SENSIBLE)
                        registros_previos = df_existente[df_existente["DNI"].astype(str).str.strip() == str(dni).strip()]
            
                        if not registros_previos.empty:
                            if "🔴 Caso Sospechoso - Derivar" in registros_previos["Estado_Triaje"].values:
                                carga_permitida = False
        
                    if not carga_permitida:
                        st.error("⛔ Operación denegada: ...")
                        st.session_state.errores_carga += 1
                    else:
                        # --- LÓGICA DE TRIAJE Y GUARDADO ---
                        valores_testeados = []
                        if od_sc > 0: valores_testeados.append(od_sc)
                        if oi_sc > 0: valores_testeados.append(oi_sc)
                        if od_cc > 0: valores_testeados.append(od_cc)
                        if oi_cc > 0: valores_testeados.append(oi_cc)

                        if len(valores_testeados) == 0:
                            valores_testeados = [10]

                        peor_vision = min(valores_testeados)

                        if peor_vision <= 7:
                            estado = "🔴 Caso Sospechoso - Derivar"
                        else:
                            estado = "🟢 Visión Normal"

                        # --- CÁLCULO DE TELEMETRÍA Y ID ÚNICO ---
                        tiempo_total_segundos = round(time.time() - st.session_state.tiempo_inicio, 1)
                        errores_cometidos = st.session_state.errores_carga
                        id_registro = str(uuid.uuid4())[:8]

                        # --- DISOCIACIÓN DE DATOS ---
                        dato_sensible = pd.DataFrame([{
                            "ID_Registro": id_registro,
                            "Nombre": nombre,
                            "Apellido": apellido,
                            "DNI": dni,
                            "Dirección": direccion,
                            "Fecha Nac": fecha_nac,
                            "Estado_Triaje": estado
                        }])
                        
                        dato_estadistico = pd.DataFrame([{
                            "ID_Registro": id_registro,
                            "Fecha Carga": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "Escuela": escuela,
                            "Edad": edad,
                            "OD_SinCorrec": od_sc,
                            "OI_SinCorrec": oi_sc,
                            "OD_ConCorrec": od_cc,
                            "OI_ConCorrec": oi_cc,
                            "Consulta_Previa": consulta_previa,
                            "Usa_Anteojos": usa_anteojos,
                            "Otro_Tratamiento": otro_tratamiento,
                            "Observaciones": observaciones,
                            "Estado_Triaje": estado
                        }])
                        
                        dato_telemetria = pd.DataFrame([{
                            "ID_Registro": id_registro,
                            "Tiempo_Carga_Segundos": tiempo_total_segundos,
                            "Errores_Operativos": errores_cometidos
                        }])

                        def guardar_csv(df, archivo):
                            if not os.path.isfile(archivo):
                                df.to_csv(archivo, index=False)
                            else:
                                df.to_csv(archivo, mode='a', header=False, index=False)

                        guardar_csv(dato_sensible, ARCHIVO_SENSIBLE)
                        guardar_csv(dato_estadistico, ARCHIVO_ESTADISTICO)
                        guardar_csv(dato_telemetria, ARCHIVO_TELEMETRIA)

                        st.session_state.form_key += 1
                        st.session_state.tiempo_inicio = time.time()
                        st.session_state.errores_carga = 0
                        
                        mostrar_cartel_resultado(estado, peor_vision)

    # -----------------------------------------
    # VISTA OFTALMÓLOGO (CIC)
    # -----------------------------------------
    elif st.session_state.rol == "CIC":
        st.title("🏥 Panel de Gestión y Derivaciones - CIC")
        st.write("Visualización de planillas digitalizadas y priorización de casos.")
        
        if os.path.isfile(ARCHIVO_SENSIBLE) and os.path.isfile(ARCHIVO_ESTADISTICO):
            # Leemos las bases de datos separadas
            df_sensible = pd.read_csv(ARCHIVO_SENSIBLE)
            df_estadistico = pd.read_csv(ARCHIVO_ESTADISTICO)
            
            # El CIC une los datos internamente para ver todo completo
            df = pd.merge(df_sensible, df_estadistico, on=["ID_Registro", "Estado_Triaje"])
            
            st.subheader("Métricas de Tamizaje")
            col1, col2, col3 = st.columns(3)
            
            total_evaluados = len(df)
            casos_sospechosos = len(df[df["Estado_Triaje"] == "🔴 Caso Sospechoso - Derivar"])
            usan_anteojos = len(df[df["Usa_Anteojos"] == "SI"])

            col1.metric("Total Evaluados", total_evaluados)
            col2.metric("Casos a Derivar", casos_sospechosos)
            col3.metric("Uso de Anteojos", usan_anteojos)

            st.divider()
            
            st.subheader("Base de Datos - Pacientes Evaluados (Confidencial)")
            st.dataframe(df.sort_values(by="Estado_Triaje"), use_container_width=True)
            
            with st.expander("Ver Base de Datos Estadística (Lo que se usaría para informes epidemiológicos)"):
                st.write("Esta tabla no contiene Nombres ni DNI. Se vincula mediante el `ID_Registro`.")
                st.dataframe(df_estadistico)
                
            if os.path.isfile(ARCHIVO_TELEMETRIA):
                with st.expander("Ver Resultados de Telemetría (Rendimiento UX/UI)"):
                    st.write("Datos de telemetría invisibles para el docente:")
                    df_telemetria = pd.read_csv(ARCHIVO_TELEMETRIA)
                    st.dataframe(df_telemetria)
            
        else:
            st.info("Aún no se han cargado planillas.")