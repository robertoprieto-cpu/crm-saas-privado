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
        try:
        creds = obtener_credenciales_google()
        client = gspread.authorize(creds)
        sheet_url = st.secrets.get("SHEET_URL", "https://docs.google.com/spreadsheets/d/1mAasQyEscIC194XW54WQF_VcyaIqJKFj/edit")
        planilla = client.open_by_url(sheet_url)
        


def subir_a_drive_temp(file_buffer, nombre_archivo, id_carpeta, creds):
    try:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(file_buffer.getvalue())
            tmp_path = tmp_file.name

        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': nombre_archivo, 'parents': [id_carpeta]}
        media = MediaFileUpload(tmp_path, resumable=True)
        
        archivo = service.files().create(
            body=file_metadata, 
            media_body=media, 
            fields='id, webViewLink',
            supportsAllDrives=True
        ).execute()
        
        try:
            service.permissions().create(
                fileId=archivo.get('id'),
                body={'role': 'reader', 'type': 'anyone'},
                supportsAllDrives=True
            ).execute()
        except Exception:
            pass
            
        os.remove(tmp_path)
        return True, archivo.get('webViewLink')
    except Exception as e:
        return False, str(e)

def enviar_telegram(mensaje):
    bot_token = st.secrets.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = st.secrets.get("TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id:
        return
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = urllib.parse.urlencode({'chat_id': chat_id, 'text': mensaje, 'parse_mode': 'HTML'}).encode('utf-8')
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        pass

# ==========================================
# SISTEMA DE AUTENTICACIÓN Y LICENCIAS
# ==========================================
planilla, hoja_leads, hoja_logistica, hoja_licencias, creds = conectar_sheets()

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False
    st.session_state["es_admin"] = False
    st.session_state["usuario_actual"] = ""

def validar_clave(clave_ingresada):
    if clave_ingresada == MASTER_KEY:
        st.session_state["autenticado"] = True
        st.session_state["es_admin"] = True
        st.session_state["usuario_actual"] = "PROPIETARIO MAESTRO"
        return True, "Acceso Propietario Concedido"
        
    licencias = hoja_licencias.get_all_records()
    for lic in licencias:
        if str(lic.get("Clave")).strip() == clave_ingresada.strip():
            if str(lic.get("Estado")).strip().lower() == "activo":
                st.session_state["autenticado"] = True
                st.session_state["es_admin"] = False
                st.session_state["usuario_actual"] = lic.get("Cliente")
                return True, f"Bienvenido {lic.get('Cliente')}"
            else:
                return False, "⚠️ Esta clave ha sido revocada o desactivada."
    return False, "❌ Clave de acceso inválida."

# ==========================================
# PANTALLA DE LOGIN
# ==========================================
if not st.session_state["autenticado"]:
    st.title("🔒 CRM Empresarial - Control de Acceso")
    st.markdown("---")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.subheader("Ingresar Licencia de Uso")
        clave_input = st.text_input("Clave de Acceso:", type="password")
        if st.button("Ingresar al Sistema", use_container_width=True):
            exito, msj = validar_clave(clave_input)
            if exito:
                st.success(msj)
                st.rerun()
            else:
                st.error(msj)
    st.stop()

# ==========================================
# INTERFAZ PRINCIPAL DEL CRM
# ==========================================
st.sidebar.title("⚡ Navegación CRM")
st.sidebar.write(f"**Usuario:** {st.session_state['usuario_actual']}")

opciones_menu = ["📊 Dashboard Leads", "📦 Logística & Remitos"]
if st.session_state["es_admin"]:
    opciones_menu.append("🔑 Control de Licencias (Admin)")

opcion = st.sidebar.radio("Ir a:", opciones_menu)

if st.sidebar.button("Cerrar Sesión"):
    st.session_state["autenticado"] = False
    st.session_state["es_admin"] = False
    st.rerun()

# ------------------------------------------
# MÓDULO 1: DASHBOARD LEADS
# ------------------------------------------
if opcion == "📊 Dashboard Leads":
    st.title("📊 Panel de Leads y Ventas")
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📥 Importar Correos No Leídos"):
            try:
                email_user = st.secrets.get("EMAIL_USUARIO", "roberto.prieto@trasorras.com")
                email_pass = st.secrets.get("EMAIL_PASSWORD", "omlv evzw gnqk ubvh")
                
                mail = imaplib.IMAP4_SSL("imap.gmail.com")
                mail.login(email_user, email_pass)
                mail.select("inbox")
                status, mensajes = mail.search(None, 'UNSEEN')
                
                if mensajes[0]:
                    id_mensajes = mensajes[0].split()[-15:]
                    nuevos_count = 0
                    for m_id in id_mensajes:
                        _, data = mail.fetch(m_id, '(RFC822)')
                        for response_part in data:
                            if isinstance(response_part, tuple):
                                msg = email.message_from_bytes(response_part[1])
                                subject = msg.get("Subject", "Sin Asunto")
                                from_str = msg.get("From", "")
                                
                                body = ""
                                if msg.is_multipart():
                                    for part in msg.walk():
                                        if part.get_content_type() == "text/plain":
                                            body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                                            break
                                else:
                                    body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
                                
                                tel_match = re.search(r'(?:Teléfono|Tel|Phone|Celular)[:\s]*([\d\+\-\s]+)', body, re.IGNORECASE)
                                tel = tel_match.group(1).strip() if tel_match else "Sin Teléfono"
                                
                                hoja_leads.append_row(["LEAD-NUEVO", from_str, "Nuevo Email", tel, subject])
                                enviar_telegram(f"🚨 <b>NUEVO LEAD</b>\n<b>De:</b> {from_str}\n<b>Tel:</b> {tel}\n<b>Asunto:</b> {subject}")
                                nuevos_count += 1
                    mail.logout()
                    st.success(f"Se importaron {nuevos_count} leads correctamente.")
                else:
                    st.info("No hay correos nuevos.")
            except Exception as e:
                st.error(f"Error procesando emails: {e}")

    with col_btn2:
        if st.button("🔄 Refrescar Tabla"):
            st.rerun()

    data_leads = hoja_leads.get_all_records()
    if data_leads:
        df_leads = pd.DataFrame(data_leads)
        st.dataframe(df_leads, use_container_width=True)
    else:
        st.write("No hay registros disponibles en la hoja de Leads.")

# ------------------------------------------
# MÓDULO 2: LOGÍSTICA Y REMITOS
# ------------------------------------------
elif opcion == "📦 Logística & Remitos":
    st.title("📦 Gestión de Logística y Remitos")
    
    with st.form("form_remito", clear_on_submit=True):
        st.subheader("Cargar Nuevo Envío")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            cliente = st.text_input("Cliente / Pedido:")
            transporte = st.text_input("Empresa de Transporte:")
        with col_f2:
            tracking = st.text_input("Número de Tracking:")
            archivo_remito = st.file_uploader("Adjuntar Remito (JPG, PNG, PDF):", type=["jpg", "jpeg", "png", "pdf"])
            
        submitted = st.form_submit_button("💾 Registrar y Subir a Google Drive")
        if submitted:
            if not cliente or not archivo_remito:
                st.warning("Completa el nombre del cliente y adjunta el remito.")
            else:
                folder_id = st.secrets.get("CARPETA_REMITOS_DRIVE_ID", "0AO1rUVlGJm3sUk9PVA")
                exito, resultado = subir_a_drive_temp(archivo_remito, archivo_remito.name, folder_id, creds)
                if exito:
                    id_ord = "ORD-" + str(len(hoja_logistica.get_all_records()) + 1)
                    hoja_logistica.append_row([id_ord, cliente, transporte, tracking, "Enviado", resultado])
                    st.success(f"✅ Remito subido a Drive correctamente: [Ver Archivo]({resultado})")
                else:
                    st.error(f"❌ Error al subir a Drive: {resultado}")

    st.markdown("---")
    st.subheader("Envíos Registrados")
    data_logistica = hoja_logistica.get_all_records()
    if data_logistica:
        df_logistica = pd.DataFrame(data_logistica)
        st.dataframe(df_logistica, use_container_width=True)

# ------------------------------------------
# MÓDULO 3: CONTROL DE LICENCIAS (SÓLO ADMIN)
# ------------------------------------------
elif opcion == "🔑 Control de Licencias (Admin)" and st.session_state["es_admin"]:
    st.title("🔑 Panel Propietario: Gestión de Claves y Clientes")
    st.warning("Solo tú tienes acceso a esta vista para crear o cancelar licencias.")
    
    with st.form("form_licencia", clear_on_submit=True):
        st.subheader("Generar Nueva Licencia de Cliente")
        col_l1, col_l2 = st.columns(2)
        with col_l1:
            nuevo_cliente = st.text_input("Nombre de la Empresa / Cliente:")
        with col_l2:
            nueva_clave = st.text_input("Clave de Acceso Única (Ej: EMPRESA_ABC_2026):")
            
        btn_crear_lic = st.form_submit_button("➕ Crear y Activar Licencia")
        if btn_crear_lic:
            if nuevo_cliente and nueva_clave:
                hoja_licencias.append_row([nueva_clave.strip(), nuevo_cliente.strip(), "Activo", str(datetime.now())])
                st.success(f"Licencia creada para '{nuevo_cliente}'. Clave: {nueva_clave}")
            else:
                st.error("Completa todos los campos.")

    st.markdown("---")
    st.subheader("Licencias Existentes y Sistema de Anulación (Kill-Switch)")
    
    licencias_data = hoja_licencias.get_all_records()
    if licencias_data:
        df_licencias = pd.DataFrame(licencias_data)
        st.dataframe(df_licencias, use_container_width=True)
        
        st.subheader("Revocar / Desactivar Acceso")
        clave_a_revocar = st.selectbox("Selecciona la clave a desactivar:", df_licencias["Clave"].tolist())
        if st.button("🔴 Revocar Acceso Inmediatamente"):
            cell = hoja_licencias.find(clave_a_revocar)
            if cell:
                # La columna 3 corresponde a "Estado"
                hoja_licencias.update_cell(cell.row, 3, "Inactivo")
                st.success(f"La clave '{clave_a_revocar}' ha sido revocada. El cliente perderá acceso de inmediato.")
                st.rerun()
