import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# CONFIGURACIÓN DE PÁGINA Y CLAVES
# ==========================================
st.set_page_config(
    page_title="CRM Pro - Ventas & Logística",
    page_icon="⚡",
    layout="wide"
)

MASTER_KEY = st.secrets.get("MASTER_KEY", "ADMIN_PROPIETARIO_2026_SECURE")

def obtener_credenciales_google():
    try:
        creds_dict = dict(st.secrets["gcp_service_account"])
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        return Credentials.from_service_account_info(creds_dict, scopes=scopes)
    except Exception as e:
        st.error(f"Error al cargar las credenciales de Google: {e}")
        st.stop()

def conectar_sheets():
    try:
        creds = obtener_credenciales_google()
        client = gspread.authorize(creds)
        
        sheet_url = st.secrets.get("SHEET_URL", "https://docs.google.com/spreadsheets/d/1mAasQyEscIC194XW54WQF_VcyaIqJKFj/edit")
        sheet_url = str(sheet_url).strip().strip('"').strip("'")
        
        planilla = client.open_by_url(sheet_url)
        hoja_leads = planilla.sheet1
        
        try:
            hoja_logistica = planilla.worksheet("Logistica")
        except Exception:
            hoja_logistica = planilla.add_worksheet(title="Logistica", rows=100, cols=20)
            hoja_logistica.append_row(["ID Pedido", "Cliente", "Transporte", "Tracking", "Estado", "Link Remito Drive"])
            
        try:
            hoja_licencias = planilla.worksheet("Licencias")
        except Exception:
            hoja_licencias = planilla.add_worksheet(title="Licencias", rows=100, cols=20)
            hoja_licencias.append_row(["Clave", "Cliente", "Estado", "Fecha Creacion"])
            hoja_licencias.append_row([MASTER_KEY, "PROPIETARIO MAESTRO", "Activo", str(datetime.now())])
            
        return planilla, hoja_leads, hoja_logistica, hoja_licencias, creds
        
    except Exception as e:
        st.error(f"Error conectando a Google Sheets. Detalle técnico: {e}")
        st.stop()