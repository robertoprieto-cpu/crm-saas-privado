import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Mi CRM - Panel de Leads", page_icon="📈", layout="wide"
)

st.title("📊 CRM de Leads en Tiempo Real")
st.write("Leads capturados automáticamente desde Gmail")

# ⚠️ PEGA AQUÍ TU ID DE GOOGLE SHEETS
SHEET_ID = "TU_ID_AQUI"

# Creamos el enlace automático para leer la hoja
URL_CSV = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"


# Función para cargar los datos (se actualiza cada 30 segundos)
@st.cache_data(ttl=30)
def cargar_leads():
    df = pd.read_csv(URL_CSV)
    return df


# Botón manual para refrescar los datos en pantalla
if st.button("🔄 Actualizar Leads"):
    st.cache_data.clear()
    st.rerun()

# Intentar cargar y mostrar la tabla
try:
    df_leads = cargar_leads()

    # Muestra el número total de contactos
    st.metric(label="Total de Leads Recibidos", value=len(df_leads))

    st.markdown("---")

    # Muestra la tabla interactiva
    st.subheader("📋 Lista de Contactos")
    st.dataframe(df_leads, use_container_width=True)

except Exception as e:
    st.error(
        f"Asegúrate de haber puesto bien el ID y que la hoja esté pública. Error: {e}"
    )
