import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from structural_drawing_funcions import structural_problems
from thermal_drawing_funcions import thermal_problems
from modal_drawing_functions import modal_problems

st.set_page_config(page_title="FEA Plotter UDO", layout="wide")

st.title("Universidad de Oriente - Núcleo Anzoátegui")
st.subheader("Departamento de Mecánica: Graficador de Elementos Finitos")

# Barra lateral para configuración
st.sidebar.header("Configuración de Análisis")
tipo_problema = st.sidebar.selectbox(
    "Seleccione el tipo de problema",
    ["Estructural", "Térmico", "Modal"]
)

uploaded_file = st.file_uploader("Cargue su archivo .eplot o .txt", type=["eplot", "txt", "csv"])

if uploaded_file:
    # Guardamos el archivo temporalmente para que tus funciones de pandas lo lean
    with open("temp_file.eplot", "wb") as f:
        f.write(uploaded_file.getbuffer())
    
    scale = st.sidebar.number_input("Factor de escala", value=1.0, step=0.1)
    
    # Creamos la figura de Matplotlib
    fig, ax = plt.subplots(figsize=(10, 6))
    
    if tipo_problema == "Estructural":
        # Llamamos a tu lógica (ajustada para retornar la fig)
        # Nota: Aquí pasamos los parámetros que tu función ya usa
        fig = structural_problems("temp_file.eplot", scale, fig, ax)
        st.pyplot(fig)
        
    elif tipo_problema == "Térmico":
        fig = thermal_problems("temp_file.eplot", scale, fig, ax)
        st.pyplot(fig)
        
    elif tipo_problema == "Modal":
        # Aquí puedes agregar un selector de modo específico
        modo = st.sidebar.selectbox("Seleccionar Modo", [1, 2, 3, 4, 5])
        fig = modal_problems("temp_file.eplot", scale, modo, fig, ax)
        st.pyplot(fig)