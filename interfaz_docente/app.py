import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Visión de Futuro", layout="wide")

ARCHIVO_DATOS = "registros_triaje_completo.csv"

# --- 1. MANEJO DE SESIÓN E INICIALIZACIÓN ---
if "conectado" not in st.session_state:
    st.session_state.conectado = False
if "rol" not in st.session_state:
    st.session_state.rol = None
if "form_key" not in st.session_state:
    st.session_state.form_key = 1

# --- 2. CARTEL EMERGENTE (MODAL) ---
@st.dialog("✅ Carga Exitosa")
def mostrar_cartel_resultado(estado_triaje, agudeza):
    st.write("Los datos del alumno han sido guardados correctamente en la base de datos.")
    
    if "Sospechoso" in estado_triaje:
        st.error(f"{estado_triaje} (Agudeza mínima detectada: {agudeza}/10)")
    else:
        st.success(f"{estado_triaje} (Agudeza mínima detectada: {agudeza}/10)")
        
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
                st.rerun()
            elif tipo_perfil == "Personal del CIC" and usuario == "cic" and contrasena == "admin":
                st.session_state.conectado = True
                st.session_state.rol = "CIC"
                st.rerun()
            else:
                st.error("⚠️ Usuario o contraseña incorrectos. Verifique sus datos.")
        
        st.divider()
        st.info("💡 **Datos de acceso:**\n- **Docente:** Usuario: `docente` | Clave: `1234`\n- **CIC:** Usuario: `cic` | Clave: `admin`")

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
            st.subheader("Datos Personales")
            col1, col2 = st.columns(2)
            with col1:
                nombre = st.text_input("Nombre:")
                dni = st.text_input("DNI:")
                fecha_nac = st.date_input("Fecha de Nac:", format="DD/MM/YYYY")
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
                if nombre == "" or apellido == "" or dni == "":
                    st.warning("⚠️ Por favor, complete al menos Nombre, Apellido y DNI.")
                else:
                    # --- NUEVA VALIDACIÓN: BLOQUEO DE DUPLICADOS CON DERIVACIÓN ---
                    carga_permitida = True
                    if os.path.isfile(ARCHIVO_DATOS):
                        df_existente = pd.read_csv(ARCHIVO_DATOS)
                        # Filtramos buscando el mismo DNI
                        registros_previos = df_existente[df_existente["DNI"].astype(str).str.strip() == str(dni).strip()]
                        
                        if not registros_previos.empty:
                            # Verificamos si en los registros de ese DNI ya existe uno marcado para derivar
                            if "🔴 Caso Sospechoso - Derivar" in registros_previos["Estado_Triaje"].values:
                                carga_permitida = False
                    
                    if not carga_permitida:
                        st.error("⛔ Operación denegada: Este alumno ya se encuentra registrado con una derivación pendiente en el CIC. No es necesario volver a cargarlo.")
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

                        nuevo_dato = pd.DataFrame([{
                            "Fecha Carga": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "Nombre": nombre,
                            "Apellido": apellido,
                            "DNI": dni,
                            "Edad": edad,
                            "Dirección": direccion,
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

                        if not os.path.isfile(ARCHIVO_DATOS):
                            nuevo_dato.to_csv(ARCHIVO_DATOS, index=False)
                        else:
                            nuevo_dato.to_csv(ARCHIVO_DATOS, mode='a', header=False, index=False)

                        st.session_state.form_key += 1
                        mostrar_cartel_resultado(estado, peor_vision)

    # -----------------------------------------
    # VISTA OFTALMÓLOGO (CIC)
    # -----------------------------------------
    elif st.session_state.rol == "CIC":
        st.title("🏥 Panel de Gestión y Derivaciones - CIC")
        st.write("Visualización de planillas digitalizadas y priorización de casos.")
        
        if os.path.isfile(ARCHIVO_DATOS):
            df = pd.read_csv(ARCHIVO_DATOS)
            
            st.subheader("Métricas de Tamizaje")
            col1, col2, col3 = st.columns(3)
            
            total_evaluados = len(df)
            casos_sospechosos = len(df[df["Estado_Triaje"] == "🔴 Caso Sospechoso - Derivar"])
            usan_anteojos = len(df[df["Usa_Anteojos"] == "SI"])

            col1.metric("Total Evaluados", total_evaluados)
            col2.metric("Casos a Derivar", casos_sospechosos)
            col3.metric("Uso de Anteojos", usan_anteojos)

            st.divider()
            
            st.subheader("Base de Datos - Pacientes Evaluados")
            st.dataframe(df.sort_values(by="Estado_Triaje"), use_container_width=True)
            
        else:
            st.info("Aún no se han cargado planillas.")