
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Visión de Futuro", layout="centered")

# Nombre del archivo que funcionará como nuestra base de datos local
ARCHIVO_DATOS = "registros_triaje.csv"

# Menú lateral para cambiar entre Docente y Oftalmólogo
st.sidebar.title("Navegación")
rol = st.sidebar.radio("Seleccione su rol:", ["Docente (Carga de Datos)", "CIC (Panel Oftalmólogo)"])

# -----------------------------------------
# PANTALLA 1: DOCENTE
# -----------------------------------------
if rol == "Docente (Carga de Datos)":
    st.title("👁️ Tamizaje Visual Escolar")
    st.write("Ingrese los datos del alumno y los resultados del test de Snellen.")

    with st.form("formulario_triaje"):
        nombre = st.text_input("Nombre y Apellido del Alumno:")
        dni = st.text_input("DNI:")
        
        st.write("**Agudeza Visual (Valores del 1 al 10)**")
        col1, col2 = st.columns(2)
        with col1:
            av_od = st.number_input("Ojo Derecho (OD):", min_value=1, max_value=10, value=10)
        with col2:
            av_oi = st.number_input("Ojo Izquierdo (OI):", min_value=1, max_value=10, value=10)
        
        enviado = st.form_submit_button("Guardar y Evaluar")

        if enviado:
            if nombre == "" or dni == "":
                st.warning("Por favor, complete todos los campos.")
            else:
                # 1. ALGORITMO DE TRIAJE
                peor_vision = min(av_od, av_oi)
                
                if peor_vision <= 7:
                    estado = "Caso Sospechoso - Derivar"
                    st.error(f"⚠️ Resultado: {estado}")
                else:
                    estado = "Visión Normal"
                    st.success(f"✅ Resultado: {estado}")
                
                # 2. GUARDAR LOS DATOS
                nuevo_dato = pd.DataFrame([{
                    "Fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Nombre": nombre,
                    "DNI": dni,
                    "AV_OD": av_od,
                    "AV_OI": av_oi,
                    "Resultado": estado
                }])

                # Si el archivo no existe lo crea con encabezados, si existe agrega la fila
                if not os.path.isfile(ARCHIVO_DATOS):
                    nuevo_dato.to_csv(ARCHIVO_DATOS, index=False)
                else:
                    nuevo_dato.to_csv(ARCHIVO_DATOS, mode='a', header=False, index=False)

# -----------------------------------------
# PANTALLA 2: OFTALMÓLOGO (CIC)
# -----------------------------------------
elif rol == "CIC (Panel Oftalmólogo)":
    st.title("🏥 Panel de Gestión - CIC")
    st.write("Listado de alumnos evaluados en las escuelas.")

    if os.path.isfile(ARCHIVO_DATOS):
        # Leer los datos guardados
        df = pd.read_csv(ARCHIVO_DATOS)
        
        # Mostrar métricas rápidas
        casos_sospechosos = len(df[df["Resultado"] == "Caso Sospechoso - Derivar"])
        st.metric(label="Casos que requieren derivación", value=casos_sospechosos)

        # Mostrar la tabla completa
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Aún no hay registros cargados por los docentes.")
        