import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import re

# ==========================================
# 1. CONFIGURACIÓN E INICIALIZACIÓN
# ==========================================
st.set_page_config(page_title="CRM & ERP Integral", layout="wide")

@st.cache_resource
def conectar_google_sheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    credentials = Credentials.from_service_account_info(creds_dict, scopes=scope)
    client = gspread.authorize(credentials)
    return client
try:
    gc = conectar_google_sheets()
    sh = gc.open_by_key("1uCTuFEK6MvR7b0U_hKjisUuGJbyDFgGDJoIObUuyFZE")
except Exception as e:
    st.error(f"Error al conectar con Google Sheets: {e}")
    st.stop()
# ==========================================
# 2. FUNCIÓN PARA CARGAR TABLAS
# ==========================================
def cargar_tabla(nombre_pestaña):
    worksheet = sh.worksheet(nombre_pestaña)
    data = worksheet.get_all_records()
    df = pd.DataFrame(data)
    # Limpia espacios invisibles en los nombres de las columnas si los hubiera
    if not df.empty:
        df.columns = df.columns.str.strip()
    return df, worksheet
# ==========================================
# 3. MENÚ LATERAL Y NAVEGACIÓN
# ==========================================
st.sidebar.title("Sistema CRM / ERP")
opcion = st.sidebar.radio(
    "Selecciona un módulo:",
    [
        "Dashboard",
        "Inventario y Precios",
        "Clientes y Cuentas Corrientes",
        "Gestión de Leads (Mail/WhatsApp)"
    ]
)

# ==========================================
# MÓDULO 1: DASHBOARD
# ==========================================
if opcion == "Dashboard":
    st.title("📊 Panel de Control General")
    
    df_cli, _ = cargar_tabla("Clientes")
    df_prod, _ = cargar_tabla("Productos")
    df_leads, _ = cargar_tabla("Leads")

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Clientes", len(df_cli) if not df_cli.empty else 0)
    col2.metric("Productos en Stock", int(df_prod["Stock_Actual"].sum()) if not df_prod.empty and "Stock_Actual" in df_prod.columns else 0)
    col3.metric("Leads Nuevos", len(df_leads[df_leads["Estado"] == "Nuevo"]) if not df_leads.empty and "Estado" in df_leads.columns else 0)

# ==========================================
# MÓDULO 2: INVENTARIO Y PRECIOS
# ==========================================
elif opcion == "Inventario y Precios":
    st.title("📦 Inventario y Lista de Precios")
    
    df_prod, ws_prod = cargar_tabla("Productos")
    tab_ver, tab_agregar, tab_editar = st.tabs(["📋 Catálogo y Stock", "➕ Añadir Producto", "✏️ Modificar Stock / Precio"])
    
    with tab_ver:
        busqueda = st.text_input("🔍 Buscar producto por nombre o código:")
        if busqueda and not df_prod.empty:
            df_filtrado = df_prod[
                df_prod['Nombre'].astype(str).str.contains(busqueda, case=False) | 
                df_prod['ID_Producto'].astype(str).str.contains(busqueda, case=False)
            ]
            st.dataframe(df_filtrado, use_container_width=True)
        else:
            st.dataframe(df_prod, use_container_width=True)

    with tab_agregar:
        with st.form("form_nuevo_producto"):
            st.subheader("Registrar Nuevo Producto")
            id_prod = st.text_input("ID / Código de Producto (Ej: PROD-001)")
            nombre_prod = st.text_input("Nombre del Producto")
            precio_prod = st.number_input("Precio de Venta ($)", min_value=0.0, format="%.2f")
            stock_prod = st.number_input("Stock Inicial", min_value=0, step=1)
            
            if st.form_submit_button("Guardar Producto"):
                if id_prod and nombre_prod:
                    ws_prod.append_row([id_prod, nombre_prod, precio_prod, stock_prod])
                    st.success(f"Producto '{nombre_prod}' registrado con éxito.")
                    st.rerun()
                else:
                    st.error("Por favor completa el ID y el Nombre del producto.")

    with tab_editar:
        if not df_prod.empty and "Nombre" in df_prod.columns:
            prod_sel = st.selectbox("Selecciona un producto para actualizar:", df_prod["Nombre"].tolist())
            if prod_sel:
                prod_info = df_prod[df_prod["Nombre"] == prod_sel].iloc[0]
                index_fila = df_prod[df_prod["Nombre"] == prod_sel].index[0] + 2
                
                with st.form("form_edit_prod"):
                    nuevo_precio = st.number_input("Nuevo Precio ($)", value=float(prod_info["Precio_Venta"]), min_value=0.0, format="%.2f")
                    nuevo_stock = st.number_input("Nuevo Stock", value=int(prod_info["Stock_Actual"]), min_value=0, step=1)
                    
                    if st.form_submit_button("Actualizar Producto"):
                        ws_prod.update_cell(index_fila, 3, nuevo_precio)
                        ws_prod.update_cell(index_fila, 4, nuevo_stock)
                        st.success("Precio y Stock actualizados correctamente.")
                        st.rerun()
        else:
            st.info("No hay productos cargados o falta definir los encabezados en Google Sheets.")

# ==========================================
# MÓDULO 3: CLIENTES Y CUENTAS CORRIENTES
# ==========================================
elif opcion == "Clientes y Cuentas Corrientes":
    st.title("💳 Cuentas Corrientes y Clientes")
    
    df_cli, ws_cli = cargar_tabla("Clientes")
    df_cta, ws_cta = cargar_tabla("Cuentas_Corrientes")
    tab_cta, tab_nuevo_cli = st.tabs(["📄 Estado de Cuenta", "👤 Registrar Cliente"])
    
    with tab_nuevo_cli:
        with st.form("form_nuevo_cliente"):
            st.subheader("Registrar Nuevo Cliente")
            id_cli = f"CLI-{int(datetime.now().timestamp())}"
            nombre_cli = st.text_input("Nombre y Apellido / Empresa")
            tel_cli = st.text_input("Teléfono (Ej: 54911...)")
            email_cli = st.text_input("Email")
            
            if st.form_submit_button("Guardar Cliente"):
                if nombre_cli:
                    ws_cli.append_row([id_cli, nombre_cli, tel_cli, email_cli, 0.0])
                    st.success(f"Cliente '{nombre_cli}' registrado exitosamente.")
                    st.rerun()
                else:
import requests
import base64

# --- FUNCIÓN PARA ENVIAR WHATSAPP ---
def enviar_whatsapp(numero, mensaje):
    EVO_URL = "https://evolution-api-latest-1-ggcm.onrender.com"
    EVO_KEY = "MiClaveSuperSeguraCRM2026"
    INSTANCE_NAME = "crm_whatsapp"

    numero_limpio = ''.join(filter(str.isdigit, str(numero)))

    headers = {
        "apikey": EVO_KEY,
        "Content-Type": "application/json"
    }
    url = f"{EVO_URL}/message/sendText/{INSTANCE_NAME}"
    payload = {
        "number": numero_limpio,
        "text": mensaje
    }

    try:
        res = requests.post(url, json=payload, headers=headers, timeout=30)
        if res.status_code in [200, 201]:
            return True, "Mensaje enviado con éxito."
        else:
            return False, f"Error de servidor ({res.status_code}): {res.text}"
    except Exception as e:
        return False, f"Error de conexión: {e}"


# --- MÓDULO DE SELECCIÓN Y ENVÍO A CLIENTE ---
st.markdown("---")
st.subheader("📲 Envío Directo de WhatsApp a Contactos")

df_actual = None
for nombre_var in ['df_contactos', 'df_cli', 'df_leads', 'df']:
    if nombre_var in st.session_state:
        df_actual = st.session_state[nombre_var]
        break
    elif nombre_var in locals():
        df_actual = locals()[nombre_var]
        break
    elif nombre_var in globals():
        df_actual = globals()[nombre_var]
        break

if df_actual is not None and hasattr(df_actual, 'empty') and not df_actual.empty:
    col_nombre = None
    for col in df_actual.columns:
        if str(col).strip().lower() in ['nombre', 'cliente', 'contacto', 'lead', 'nombres', 'customer']:
            col_nombre = col
            break

    if not col_nombre and len(df_actual.columns) > 0:
        col_nombre = df_actual.columns[0]

    lista_clientes = df_actual[col_nombre].dropna().astype(str).tolist() if col_nombre else []

    cliente_sel = st.selectbox("Seleccionar Cliente:", lista_clientes)

    if cliente_sel:
        col_telefono = None
        for col in df_actual.columns:
            if str(col).strip().lower() in ['telefono', 'teléfono', 'celular', 'phone', 'mobile', 'wa', 'whatsapp']:
                col_telefono = col
                break

        if not col_telefono and len(df_actual.columns) > 1:
            col_telefono = df_actual.columns[1]

        fila = df_actual[df_actual[col_nombre].astype(str) == cliente_sel].iloc[0]
        telefono_cliente = fila.get(col_telefono, '') if col_telefono else ''

        st.info(f"📞 **Teléfono:** {telefono_cliente}")

        mensaje_defecto = f"Hola {cliente_sel}, te escribimos desde el CRM para brindarte novedades sobre tu consulta. ¡Quedamos a tu disposición!"
        mensaje_personalizado = st.text_area("Mensaje a enviar:", value=mensaje_defecto, height=120)

        if st.button("🚀 Enviar WhatsApp al Cliente", type="primary"):
            if telefono_cliente and mensaje_personalizado:
                exito, resp = enviar_whatsapp(telefono_cliente, mensaje_personalizado)
                if exito:
                    st.success(f"✅ ¡Mensaje enviado a {cliente_sel}!")
                else:
                    st.error(f"⚠️ {resp}")
            else:
                st.warning("Verifica que el cliente tenga un número asignado.")
else:
    st.info("💡 Carga o selecciona una lista de clientes en el CRM para habilitar el envío rápido.")


# --- CONFIGURACIÓN DE CONEXIÓN Y QR ---
with st.expander("⚙️ Estado de la Conexión de WhatsApp"):
    st.write("Administra la instancia y genera el QR si requieres reconectar.")
    EVO_URL = "https://evolution-api-latest-1-ggcm.onrender.com"
    EVO_KEY = "MiClaveSuperSeguraCRM2026"
    INSTANCE_NAME = "crm_whatsapp"
    headers = {"apikey": EVO_KEY, "Content-Type": "application/json"}

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Inicializar Instancia"):
            payload = {"instanceName": INSTANCE_NAME, "qrcode": True, "integration": "WHATSAPP-BAILEYS"}
            try:
                res = requests.post(f"{EVO_URL}/instance/create", json=payload, headers=headers, timeout=30)
                st.info(f"Estado de instancia: {res.status_code}")
            except Exception as err:
                st.error(f"Error: {err}")

    with c2:
        if st.button("Generar Código QR"):
            try:
                res = requests.get(f"{EVO_URL}/instance/connect/{INSTANCE_NAME}", headers=headers, timeout=30)
                if res.status_code == 200:
                    data = res.json()
                    qr_code_base64 = data.get("base64") or data.get("code")
                    if qr_code_base64:
                        if "," in qr_code_base64:
                            qr_code_base64 = qr_code_base64.split(",")[1]
                        st.image(base64.b64decode(qr_code_base64), width=300)
                    else:
                        st.success("¡Tu WhatsApp está conectado y listo!")
            except Exception as err:
                st.error(f"Error: {err}")
