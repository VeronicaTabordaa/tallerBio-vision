import streamlit as st
import pandas as pd
import os
import time
import uuid
from datetime import datetime

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

# Variables para la Telemetría
if "tiempo_inicio" not in st.session_state:
    st.session_state.tiempo_inicio = time.time()
if "errores_carga" not in st.session_state:
    st.session_state.errores_carga = 0

# --- 2. CARTEL EMERGENTE (MODAL) ---
@st.dialog("✅ Carga Exitosa")
def mostrar_cartel_resultado(estado_triaje, agudeza, tiempo, errores):
    st.write("Los datos han sido disociados y guardados de forma segura.")
    
    if "Sospechoso" in estado_triaje:
        st.error(f"{estado_triaje} (Agudeza mínima: {agudeza}/10)")
    else:
        st.success(f"{estado_triaje} (Agudeza mínima: {agudeza}/10)")
        
    st.caption(f"⏱️ Telemetría: Carga completada en {tiempo} segundos con {errores} fallos de validación.")
        
    if st.button("OK - Cargar nuevo alumno", type="primary", use_container_width=True):
        st.rerun()

# --- 3. PANTALLA DE INICIO DE SESIÓN ---
if not st.session_state.conectado:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("🔐 Acceso al Sistema")
        st.markdown("Plataforma **Visión de Futuro**")
        
        tipo_perfil = st.selectbox("Seleccione su perfil de ingreso:", ["Docente", "Personal del CIC"])
        usuario = st.text_input("Usuario:")
        contrasena = st.text_input("Contraseña:", type="password")
        
        if st.button("Iniciar Sesión", use_container_width=True):
            if tipo_perfil == "Docente" and usuario == "docente" and contrasena == "1234":
                st.session_state.conectado = True
                st.session_state.rol = "Docente"
                # Reseteamos el reloj al entrar
                st.session_state.tiempo_inicio = time.time() 
                st.rerun()
            elif tipo_perfil == "Personal del CIC" and usuario == "cic" and contrasena == "admin":
                st.session_state.conectado = True
                st.session_state.rol = "CIC"
                st.rerun()
            else:
                st.error("⚠️ Usuario o contraseña incorrectos. Verifique sus datos.")

# --- 4. SISTEMA PRINCIPAL ---
else:
    st.sidebar.title("Opciones")
    st.sidebar.success(f"👤 Conectado como: **{st.session_state.rol}**")
    
    if st.sidebar.button("Cerrar Sesión"):
        st.session_state.conectado = False
        st.session_state.rol = None
        st.rerun()

    # -----------------------------------------
    # VISTA DOCENTE
    # -----------------------------------------
    if st.session_state.rol == "Docente":
        st.title("📝 Planilla de Tamizaje Visual")
        st.write("Complete los datos extraídos de la planilla física.")

        with st.form(f"formulario_completo_{st.session_state.form_key}"):
            st.subheader("Datos Personales y Escolares")
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre:")
                dni = st.text_input("DNI:")
                fecha_nac = st.date_input("Fecha de Nac:", format="DD/MM/YYYY")
                escuela = st.text_input("Institución Escolar:") # Nuevo campo para estadística
            with col2:
                apellido = st.text_input("Apellido:")
                edad = st.number_input("Edad:", min_value=4, max_value=20, value=6, step=1)
                direccion = st.text_input("Dirección:")

            st.subheader("Agudeza Visual")
            st.info("Ingrese valores del 1 al 10. Si no usa corrección, deje los campos 'Con Corrección' en 0.")
            
            col_sc, col_cc = st.columns(2)
            with col_sc:
                st.markdown("**Sin Corrección**")
                col_sc1, col_sc2 = st.columns(2)
                with col_sc1:
                    od_sc = st.number_input("OD (Sin Correc.):", min_value=0, max_value=10, value=10)
                with col_sc2:
                    oi_sc = st.number_input("OI (Sin Correc.):", min_value=0, max_value=10, value=10)
            
            with col_cc:
                st.markdown("**Con Corrección (Lentes)**")
                col_cc1, col_cc2 = st.columns(2)
                with col_cc1:
                    od_cc = st.number_input("OD (Con Correc.):", min_value=0, max_value=10, value=0)
                with col_cc2:
                    oi_cc = st.number_input("OI (Con Correc.):", min_value=0, max_value=10, value=0)

            st.subheader("Antecedentes")
            col_ant1, col_ant2 = st.columns(2)
            with col_ant1:
                consulta_previa = st.radio("Consultó Anteriormente con un Oftalmólogo:", ["SI", "NO"], index=1)
            with col_ant2:
                usa_anteojos = st.radio("Usa Anteojos:", ["SI", "NO"], index=1)

            enviado = st.form_submit_button("Guardar y Evaluar")

            if enviado:
                if nombre == "" or apellido == "" or dni == "" or escuela == "":
                    st.warning("⚠️ Por favor, complete Nombre, Apellido, DNI y Escuela.")
                    # Telemetría: Sumamos un error operativo
                    st.session_state.errores_carga += 1 
                else:
                    carga_permitida = True
                    if os.path.isfile(ARCHIVO_SENSIBLE):
                        df_existente = pd.read_csv(ARCHIVO_SENSIBLE)
                        registros_previos = df_existente[df_existente["DNI"].astype(str).str.strip() == str(dni).strip()]
                        if not registros_previos.empty and "🔴 Caso Sospechoso - Derivar" in registros_previos["Estado_Triaje"].values:
                            carga_permitida = False
                            st.session_state.errores_carga += 1
                    
                    if not carga_permitida:
                        st.error("⛔ Operación denegada: Este alumno ya tiene una derivación pendiente.")
                    else:
                        # --- CÁLCULO DE TELEMETRÍA ---
                        tiempo_total_segundos = round(time.time() - st.session_state.tiempo_inicio, 1)
                        errores_cometidos = st.session_state.errores_carga
                        
                        # --- GENERACIÓN DE ID ÚNICO ---
                        id_registro = str(uuid.uuid4())[:8] # Genera un código aleatorio (ej: "4a2b9c1f")

                        # --- LÓGICA DE TRIAJE ---
                        valores_testeados = [v for v in [od_sc, oi_sc, od_cc, oi_cc] if v > 0]
                        if len(valores_testeados) == 0: valores_testeados = [10]
                        peor_vision = min(valores_testeados)

                        estado = "🔴 Caso Sospechoso - Derivar" if peor_vision <= 7 else "🟢 Visión Normal"

                        # --- GUARDADO 1: DATOS SENSIBLES (IDENTIFICATORIOS) ---
                        dato_sensible = pd.DataFrame([{
                            "ID_Registro": id_registro,
                            "Nombre": nombre,
                            "Apellido": apellido,
                            "DNI": dni,
                            "Dirección": direccion,
                            "Fecha Nac": fecha_nac,
                            "Estado_Triaje": estado
                        }])
                        
                        # --- GUARDADO 2: DATOS ESTADÍSTICOS (ANÓNIMOS) ---
                        dato_estadistico = pd.DataFrame([{
                            "ID_Registro": id_registro,
                            "Fecha Carga": datetime.now().strftime("%d/%m/%Y"),
                            "Escuela": escuela,
                            "Edad": edad,
                            "OD_SinCorrec": od_sc,
                            "OI_SinCorrec": oi_sc,
                            "OD_ConCorrec": od_cc,
                            "OI_ConCorrec": oi_cc,
                            "Usa_Anteojos": usa_anteojos,
                            "Estado_Triaje": estado
                        }])
                        
                        # --- GUARDADO 3: TELEMETRÍA ---
                        dato_telemetria = pd.DataFrame([{
                            "ID_Registro": id_registro,
                            "Tiempo_Carga_Segundos": tiempo_total_segundos,
                            "Errores_Operativos": errores_cometidos
                        }])

                        # Funciones para guardar en CSV
                        def guardar_csv(df, archivo):
                            if not os.path.isfile(archivo):
                                df.to_csv(archivo, index=False)
                            else:
                                df.to_csv(archivo, mode='a', header=False, index=False)

                        guardar_csv(dato_sensible, ARCHIVO_SENSIBLE)
                        guardar_csv(dato_estadistico, ARCHIVO_ESTADISTICO)
                        guardar_csv(dato_telemetria, ARCHIVO_TELEMETRIA)

                        # Reiniciamos las variables para el próximo alumno
                        st.session_state.form_key += 1
                        st.session_state.tiempo_inicio = time.time()
                        st.session_state.errores_carga = 0
                        
                        mostrar_cartel_resultado(estado, peor_vision, tiempo_total_segundos, errores_cometidos)

    # -----------------------------------------
    # VISTA OFTALMÓLOGO (CIC)
    # -----------------------------------------
    elif st.session_state.rol == "CIC":
        st.title("🏥 Panel de Gestión - CIC (Acceso Restringido)")
        
        if os.path.isfile(ARCHIVO_SENSIBLE) and os.path.isfile(ARCHIVO_ESTADISTICO):
            # Leemos las bases de datos separadas
            df_sensible = pd.read_csv(ARCHIVO_SENSIBLE)
            df_estadistico = pd.read_csv(ARCHIVO_ESTADISTICO)
            
            # El sistema del CIC "cruza" internamente la información usando el ID único para que el oftalmólogo vea todo
            df_completo = pd.merge(df_sensible, df_estadistico, on=["ID_Registro", "Estado_Triaje"])
            
            st.subheader("Métricas Generales")
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Evaluados", len(df_completo))
            col2.metric("Casos a Derivar", len(df_completo[df_completo["Estado_Triaje"] == "🔴 Caso Sospechoso - Derivar"]))
            col3.metric("Escuelas Evaluadas", df_completo["Escuela"].nunique())

            st.divider()
            st.subheader("Base de Datos Consolidada (Confidencial)")
            st.dataframe(df_completo.sort_values(by="Estado_Triaje"), use_container_width=True)
            
            # Muestra de la tabla anónima para ejemplificar en la presentación
            with st.expander("Ver Base de Datos Estadística (Lo que se usaría para informes epidemiológicos)"):
                st.write("Esta tabla no contiene Nombres ni DNI. Se vincula mediante el `ID_Registro`.")
                st.dataframe(df_estadistico)
                
            # Muestra de la tabla de telemetría
            if os.path.isfile(ARCHIVO_TELEMETRIA):
                with st.expander("Ver Resultados de Telemetría (Rendimiento UX/UI)"):
                    df_telemetria = pd.read_csv(ARCHIVO_TELEMETRIA)
                    st.dataframe(df_telemetria)
        else:
            st.info("Aún no se han cargado planillas.")