import requests
import io
from pypdf import PdfReader

# Configuración
PDF_URL = "https://ejemplo.com/diario.pdf"
KEYWORDS = ["palabra1", "palabra2"]
TELEGRAM_TOKEN = "tu_token"
TELEGRAM_CHAT_ID = "tu_id"

def check_pdf():
    try:
        response = requests.get(PDF_URL, timeout=10)
        response.raise_for_status()
        
        with io.BytesIO(response.content) as f:
            reader = PdfReader(f)
            text = "".join(page.extract_text() for page in reader.pages).lower()
            
            found = [word for word in KEYWORDS if word.lower() in text]
            
            if found:
                message = f"🎯 ¡Encontrado! El PDF contiene: {', '.join(found)}"
                send_notification(message)
    except Exception as e:
        print(f"Error: {e}")

def send_notification(msg):
    # Ejemplo con Telegram, pero podrías usar un simple print o Webhook
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

if __name__ == "__main__":
    check_pdf()