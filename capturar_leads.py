import imaplib
import email
from email.header import decode_header
import re
import os
import json
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. CONEXIÓN A GOOGLE SHEETS
# ==========================================
def conectar_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    # Leer JSON de credenciales desde variables de entorno
    json_creds = os.environ.get("GCP_SERVICE_ACCOUNT_JSON")
    
    if json_creds:
        creds_dict = json.loads(json_creds)
    else:
        # Fallback por si lo ejecutas localmente
        with open("credenciales.json", "r") as f:
            creds_dict = json.load(f)

    # Corregir saltos de línea en la clave privada
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")

    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    gc = gspread.authorize(creds)
    
    # Asegúrate de que "CRM_Database" sea el nombre exacto de tu libro en Google Sheets
    return gc.open("CRM_Database").worksheet("Leads")

# ==========================================
# 2. ESCANEO Y PROCESAMIENTO DE EMAILS
# ==========================================
def procesar_emails_leads():
    IMAP_SERVER = "imap.gmail.com"
    EMAIL_USER = os.environ.get("EMAIL_USER")
    EMAIL_PASS = os.environ.get("EMAIL_PASS")

    if not EMAIL_USER or not EMAIL_PASS:
        print("Error: No se encontraron las credenciales de correo (EMAIL_USER / EMAIL_PASS).")
        return

    try:
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USER, EMAIL_PASS)
        mail.select("inbox")

        # Buscar correos no leídos
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

                    from_str = msg.get("From")

                    # Decodificar Cuerpo
                    body = ""
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                body = part.get_payload(decode=True).decode(errors="ignore")
                                break
                    else:
                        body = msg.get_payload(decode=True).decode(errors="ignore")

                    # Filtrar por palabra clave "lead" o "leads"
                    texto_completo = f"{subject} {body}".lower()
                    if "lead" in texto_completo or "leads" in texto_completo:
                        tel_match = re.search(r'\+?\d[\d\s\-]{8,15}\d', body)
                        telefono = tel_match.group(0) if tel_match else "No detectado"

                        lead_id = f"LEAD-{int(datetime.now().timestamp())}"
                        fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M")

                        # Insertar fila en Google Sheets
                        sheet_leads.append_row([
                            lead_id,
                            fecha_actual,
                            from_str,
                            subject,
                            body[:300] + "...",
                            "Nuevo",
                            telefono
                        ])
                        print(f"✅ Lead guardado con éxito: {subject}")

        mail.logout()

    except Exception as e:
        print(f"Error procesando correos: {e}")

if __name__ == "__main__":
    procesar_emails_leads()
