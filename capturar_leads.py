import imaplib
import email
from email.header import decode_header
import re
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. CONEXIÓN A GOOGLE SHEETS
# ==========================================
def conectar_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    # Si lo ejecutas localmente usa tu json, o carga los secretos de Streamlit
    creds = Credentials.from_service_account_file("credenciales.json", scopes=scope)
    gc = gspread.authorize(creds)
    return gc.open("CRM_Database").worksheet("Leads")

# ==========================================
# 2. ESCANEO Y PROCESAMIENTO DE EMAILS
# ==========================================
def procesar_emails_leads():
    # Configuración de tu proveedor de correo (Ejemplo: Gmail)
    IMAP_SERVER = "imap.gmail.com"
    EMAIL_USER = "tu_correo@gmail.com" 
    EMAIL_PASS = "xxxx xxxx xxxx xxxx"  # Contraseña de aplicación de 16 caracteres

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Buscar correos NO LEÍDOS (UNSEEN)
        status, messages = mail.search(None, 'UNSEEN')
        email_ids = messages[0].split()

        if not email_ids:
            print("No hay correos nuevos sin leer.")
            return

        sheet_leads = conectar_sheets()

        for e_id in email_ids:
            _, msg_data = mail.fetch(e_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    msg = email.message_from_bytes(response_part[1])
                    
                    # Decodificar Asunto
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")

                    # Obtener Remitente
                    from_str = msg.get("From")

                    # Extraer Cuerpo del mensaje
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            content_type = part.get_content_type()
                            if content_type == "text/plain":
                                body = part.get_payload(decode=True).decode()
                                break
                    else:
                        body = msg.get_payload(decode=True).decode()

                    # Verificar si contiene la palabra clave 'lead' o 'leads'
                    texto_completo = f"{subject} {body}".lower()
                    if "lead" in texto_completo or "leads" in texto_completo:
                        
                        # Extraer un teléfono si viene en el texto (Regex para formato numérico)
                        tel_match = re.search(r'\+?\d[\d\s\-]{8,15}\d', body)
                        telefono = tel_match.group(0) if tel_match else "No detectado"

                        # Generar ID de Lead único
                        lead_id = f"LEAD-{int(datetime.now().timestamp())}"
                        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")

                        # Insertar en Google Sheets
                        sheet_leads.append_row([
                            lead_id,
                            fecha_actual,
                            from_str,
                            subject,
                            body[:200] + "...", # Guardar un extracto
                            "Nuevo",
                            telefono
                        ])
                        print(f"✅ Lead registrado: {subject}")

        mail.logout()

    except Exception as e:
        print(f"Error procesando correos: {e}")

if __name__ == "__main__":
    procesar_emails_leads()
