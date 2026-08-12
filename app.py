import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. CONFIGURACIÓN DE PÁGINA Y CLAVES
# ==========================================
st.set_page_config(
    page_title="CRM Pro - Ventas & Logística",
    page_icon="⚡",
    layout="wide"
)

MASTER_KEY = st.secrets.get("MASTER_KEY", "ADMIN_PROPIETARIO_2026_SECURE")

# ==========================================
# 2. FUNCIONES DE CONEXIÓN A GOOGLE
# ==========================================
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
    # 1. Autorización de seguridad
    try:
        creds = obtener_credenciales_google()
        client = gspread.authorize(creds)
    except Exception as e:
        st.error(f"🚨 Error 1 - Fallo en credenciales: {e}")
        st.stop()
        
    # 2. Conexión a la planilla
    try:
        # Aquí mantén tu URL completa (la que pusiste en el paso anterior)
        sheet_url = "PEGA_AQUI_TU_URL_COMPLETA_Y_LARGA"
        planilla = client.open_by_url(sheet_url)
    except Exception as e:
        st.error(f"🚨 Error 2 - Fallo al abrir la planilla: {e}")
        st.stop()
        
    # 3. Lectura / Creación de la hoja principal
    try:
        hoja_leads = planilla.sheet1
    except Exception as e:
        st.error(f"🚨 Error 3 - Fallo al leer la hoja principal (Hoja 1): {e}")
        st.stop()

    # 4. Creación Segura de Logistica
    try:
        hoja_logistica = planilla.worksheet("Logistica")
    except gspread.exceptions.WorksheetNotFound:
        # Si no existe, la creamos (sin comillas en los números)
        hoja_logistica = planilla.add_worksheet(title="Logistica", rows=100, cols=20)
        hoja_logistica.append_row(["ID Pedido", "Cliente", "Transporte", "Tracking", "Estado", "Link Remito Drive"])
    except Exception as e:
        st.error(f"🚨 Error al procesar Logística: {e}")
        st.stop()
        
    # 5. Creación Segura de Licencias
    try:
        hoja_licencias = planilla.worksheet("Licencias")
    except gspread.exceptions.WorksheetNotFound:
        hoja_licencias = planilla.add_worksheet(title="Licencias", rows=100, cols=20)
        hoja_licencias.append_row(["Clave", "Cliente", "Estado", "Fecha Creacion"])
        hoja_licencias.append_row([MASTER_KEY, "PROPIETARIO MAESTRO", "Activo", str(datetime.now())])
    except Exception as e:
        st.error(f"🚨 Error al procesar Licencias: {e}")
        st.stop()
        
    return planilla, hoja_leads, hoja_logistica, hoja_licencias, creds
    return planilla, hoja_leads, hoja_logistica, hoja_licencias, creds

# ==========================================
# 3. SISTEMA DE LOGIN (CANDADO)
# ==========================================
def check_password():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.title("🔒 Acceso Seguro - CRM")
            st.markdown("Por favor, ingresa tu clave maestra para continuar.")
            
            clave_ingresada = st.text_input("Contraseña", type="password")
            if st.button("Ingresar", use_container_width=True):
                if clave_ingresada == MASTER_KEY:
                    st.session_state["logged_in"] = True
                    st.rerun()
                else:
                    st.error("❌ Clave incorrecta. Intenta nuevamente.")
        return False
    return True

# ==========================================
# 4. INTERFAZ PRINCIPAL DEL CRM
# ==========================================
def main():
    if not check_password():
        return
        
    # Menú lateral
    st.sidebar.title("⚡ Panel de Navegación")
    menu = st.sidebar.radio("Ir a la sección:", ["Ventas y Leads", "Logística y Envíos", "Licencias"])
    
    st.sidebar.markdown("---")
    if st.sidebar.button("Salir / Cerrar Sesión"):
        st.session_state["logged_in"] = False
        st.rerun()
        
    # Mensaje de carga
    with st.spinner("Conectando con Google Sheets y Drive..."):
        try:
            planilla, hoja_leads, hoja_logistica, hoja_licencias, creds = conectar_sheets()
        except Exception:
            st.stop()

    # Pantallas según el menú elegido
    if menu == "Ventas y Leads":
        st.header("📊 Gestión de Ventas y Leads")
        st.info("Datos actuales en tu Base de Datos (Hoja 1):")
        try:
            datos = hoja_leads.get_all_records()
            if datos:
                st.dataframe(pd.DataFrame(datos), use_container_width=True)
            else:
                st.warning("La hoja principal está vacía. Añade datos en tu Google Sheets.")
        except Exception as e:
            st.error(f"No se pudieron cargar los datos de Leads: {e}")

    elif menu == "Logística y Envíos":
        st.header("📦 Control de Logística")
        try:
            datos_log = hoja_logistica.get_all_records()
            if datos_log:
                st.dataframe(pd.DataFrame(datos_log), use_container_width=True)
            else:
                st.warning("No hay pedidos registrados en Logística.")
        except Exception:
            pass

    elif menu == "Licencias":
        st.header("🔑 Administración de Licencias")
        try:
            datos_lic = hoja_licencias.get_all_records()
            if datos_lic:
                st.dataframe(pd.DataFrame(datos_lic), use_container_width=True)
            else:
                st.warning("No hay licencias registradas.")
        except Exception:
            pass

if __name__ == "__main__":
    main()
