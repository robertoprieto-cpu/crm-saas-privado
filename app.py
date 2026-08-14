import pandas as pd
import streamlit as st

# Configuración básica
st.set_page_config(
    page_title="Mi CRM - Panel de Leads", page_icon="📈", layout="wide"
)

st.title("📊 CRM de Leads en Tiempo Real")
st.write("Leads capturados automáticamente desde Gmail")

# ⚠️ PEGA AQUÍ TU ENLACE COMPLETO DE "PUBLICAR EN LA WEB"
URL_CSV = "PEGA_AQUI_TU_ENLACE_DE_PUBLICAR_EN_LA_WEB"


# Función de carga directa
def cargar_datos():
    return pd.read_csv(URL_CSV)


# Intentar mostrar los datos
try:
    df_leads = cargar_datos()

    st.metric(label="Total de Leads Recibidos", value=len(df_leads))
    st.markdown("---")
    st.subheader("📋 Lista de Contactos")
    st.dataframe(df_leads, use_container_width=True)

except Exception as e:
    st.warning("Cargando datos desde Google Sheets...")
    st.error(f"Detalle técnico del error: {e}")
