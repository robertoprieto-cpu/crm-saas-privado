import pandas as pd
import streamlit as st

# Configuración básica
st.set_page_config(
    page_title="Mi CRM - Panel de Leads", page_icon="📈", layout="wide"
)

st.title("📊 CRM de Leads en Tiempo Real")
st.write("Leads capturados automáticamente desde Gmail")

# ⚠️ PEGA AQUÍ TU ENLACE COMPLETO DE "PUBLICAR EN LA WEB"
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRU1E0XEW3vl9qTtaRQvPapZpPjQyoxFXKSg3fq3ac1Jy3Tym_ZsZoyKyrEXQKGc9-_PBH3IL775do0/pub?output=csv"


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
