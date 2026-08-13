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
                    st.error("El nombre del cliente es obligatorio.")

    with tab_cta:
        if not df_cli.empty:
            cliente_sel = st.selectbox("Seleccionar Cliente:", df_cli["Nombre"].tolist())
            
            if cliente_sel:
                info_cli = df_cli[df_cli["Nombre"] == cliente_sel].iloc[0]
                id_cliente = info_cli["ID_Cliente"]
                
                movs = df_cta[df_cta["ID_Cliente"] == id_cliente] if not df_cta.empty else pd.DataFrame()
                
                total_debe = float(movs["Debe"].sum()) if not movs.empty and "Debe" in movs.columns else 0.0
                total_haber = float(movs["Haber"].sum()) if not movs.empty and "Haber" in movs.columns else 0.0
                saldo_actual = total_debe - total_haber
                
                col_info1, col_info2, col_info3 = st.columns(3)
                col_info1.metric("Total Ventas a Crédito (Debe)", f"${total_debe:,.2f}")
                col_info2.metric("Total Pagos (Haber)", f"${total_haber:,.2f}")
                col_info3.metric("Saldo Deudor Actual", f"${saldo_actual:,.2f}")
                
                st.subheader("Historial de Movimientos")
                if not movs.empty:
                    st.dataframe(movs[["Fecha", "Concepto", "Debe", "Haber", "Saldo"]], use_container_width=True)
                else:
                    st.info("Este cliente no registra movimientos aún.")
                
                st.divider()
                st.subheader("Registrar Nuevo Movimiento")
                with st.form("form_movimiento"):
                    concepto = st.text_input("Concepto / Detalle (Ej: Venta Factura #1024)")
                    tipo_mov = st.radio("Tipo de Operación:", ["Venta a Crédito (Suma a la Deuda - Debe)", "Pago / Cobro (Resta a la Deuda - Haber)"])
                    monto = st.number_input("Monto ($)", min_value=0.01, format="%.2f")
                    
                    if st.form_submit_button("Registrar Movimiento en Cta Cte"):
                        id_mov = f"MOV-{int(datetime.now().timestamp())}"
                        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")
                        
                        debe = monto if "Venta" in tipo_mov else 0.0
                        haber = monto if "Pago" in tipo_mov else 0.0
                        nuevo_saldo = saldo_actual + debe - haber
                        
                        ws_cta.append_row([
                            id_mov,
                            id_cliente,
                            fecha_actual,
                            concepto,
                            debe,
                            haber,
                            nuevo_saldo
                        ])
                        
                        st.success("Movimiento registrado en la cuenta corriente.")
                        st.rerun()
        else:
            st.info("No hay clientes registrados en el sistema.")

# ==========================================
# MÓDULO 4: GESTIÓN DE LEADS
# ==========================================
elif opcion == "Gestión de Leads (Mail/WhatsApp)":
    st.title("📥 Gestión y Calificación de Leads")

    df_leads, ws_leads = cargar_tabla("Leads")

    if df_leads.empty:
        st.info("No hay leads registrados aún.")
    else:
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Leads", len(df_leads))
        col2.metric("Nuevos", len(df_leads[df_leads["Estado"] == "Nuevo"]) if "Estado" in df_leads.columns else 0)
        col3.metric("Contactados", len(df_leads[df_leads["Estado"] == "Contactado"]) if "Estado" in df_leads.columns else 0)

        st.divider()

        filtro = st.selectbox("Filtrar por estado:", ["Todos", "Nuevo", "Contactado", "Ganado", "Perdido"])
        df_mostrar = df_leads if filtro == "Todos" else df_leads[df_leads["Estado"] == filtro]

        for index, row in df_mostrar.iterrows():
            with st.expander(f"🔴 {row.get('Estado', 'Nuevo')} | {row.get('Asunto', 'Sin Asunto')} - {row.get('Remitente', '')}"):
                st.write(f"**Fecha:** {row.get('Fecha', '')}")
                st.write(f"**Teléfono:** {row.get('Telefono', 'No detectado')}")
                st.caption(f"**Mensaje:** {row.get('Mensaje', '')}")


import requests
import base64

st.markdown("---")
with st.expander("⚙️ Configuración y Conexión de WhatsApp"):
    st.write("Desde aquí puedes gestionar tu conexión a WhatsApp y probar el envío de mensajes.")

    # Asegúrate de que esta sea tu clave real si la cambiaste
    EVO_URL = "https://evolution-api-latest-1-ggcm.onrender.com"
    EVO_KEY = "MiClaveSuperSeguraCRM2026"
    INSTANCE_NAME = "crm_whatsapp"

    headers = {
        "apikey": EVO_KEY,
        "Content-Type": "application/json"
    }

    col1, col2 = st.columns(2)

    with col1:
        if st.button("1. Inicializar Instancia"):
            payload = {
                "instanceName": INSTANCE_NAME,
                "qrcode": True,
                "integration": "WHATSAPP-BAILEYS"
            }
            try:
                res = requests.post(f"{EVO_URL}/instance/create", json=payload, headers=headers, timeout=60)
                if res.status_code in [200, 201]:
                    st.success("Instancia inicializada correctamente.")
                else:
                    st.info(f"Instancia lista. (Código {res.status_code})")
            except Exception as err:
                st.error(f"Error: {err}")

    with col2:
        if st.button("2. Generar Código QR"):
            try:
                res = requests.get(f"{EVO_URL}/instance/connect/{INSTANCE_NAME}", headers=headers, timeout=60)
                if res.status_code == 200:
                    data = res.json()
                    qr_code_base64 = data.get("base64") or data.get("code")
                    if qr_code_base64:
                        if "," in qr_code_base64:
                            qr_code_base64 = qr_code_base64.split(",")[1]
                        img_bytes = base64.b64decode(qr_code_base64)
                        st.image(img_bytes, caption="Escanea este QR", width=300)
                    else:
                        st.success("¡Tu WhatsApp ya está conectado!")
                else:
                    st.error("Primero inicializa la instancia.")
            except Exception as err:
                st.error(f"Error: {err}")

    st.markdown("---")
    st.write("### 🚀 Prueba de Envío de Mensaje")
    
    # Formato Internacional: Código de país (54) + 9 (celular en Arg) + Código de área (sin 0) + Número (sin 15)
    test_number = st.text_input("Número de WhatsApp destino (Ej. para Argentina: 5491123456789):")
    test_message = st.text_area("Mensaje a enviar:", "¡Hola! Este es mi primer mensaje automático desde mi nuevo CRM. 🚀")
    
    if st.button("3. Enviar Mensaje de Prueba"):
        if test_number and test_message:
            send_url = f"{EVO_URL}/message/sendText/{INSTANCE_NAME}"
            payload_send = {
                "number": test_number,
                "text": test_message
            }
            try:
                res_send = requests.post(send_url, json=payload_send, headers=headers, timeout=60)
                if res_send.status_code in [200, 201]:
                    st.success("✅ ¡Mensaje enviado con éxito! Revisa tu celular.")
                else:
                    st.error(f"⚠️ Error al enviar: {res_send.text}")
            except Exception as e:
                st.error(f"⚠️ Error de conexión: {e}")
        else:
            st.warning("Por favor, completa el número y el mensaje.")
