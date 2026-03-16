import requests
import io
import os
import unicodedata
import re
import logging

from pypdf import PdfReader
from dotenv import load_dotenv

from models import Offer

load_dotenv()

# Configuración
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_TOKEN_CHAT_IDS = os.getenv('TELEGRAM_CHAT_IDS')
URLS = os.getenv('URLS')
KEYWORDS = os.getenv('KEYWORDS')
ENV = os.getenv('ENV')

url_array = []
keywords_array = []
chat_id_array = []
message_list = []
offers = []
filtered_offers = []

def check_url(target):
    try:
        print(f"Checking URL: {target}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(target, headers=headers, timeout=15)
        response.raise_for_status()

        scrappe_content(response)
    except Exception as e:
        print(f"Error checking the URL {target}: {e}")

def scrappe_content(response: requests.Response):
    try:
        content_type = response.headers.get('Content-Type', '').lower()

        if "application/pdf" in content_type:
            scrappe_pdf(response.content)
        elif "application/json" in content_type:
            scrappe_json(response.json())
        else:
            print(f"Content-type not recognised: {content_type}")
                
    except Exception as e:
        print(f"Error while scrapping content: {e}")

def scrappe_pdf(content):
    global offers
    try:
        text_lines = []

        with io.BytesIO(content) as f:
            reader = PdfReader(f)

            for page in reader.pages:
                page_text = page.extract_text(extraction_mode="layout")
                page_lines = page_text.splitlines()
                
                for line in page_lines:
                    if line.strip() and not line.isspace():
                        text_lines.append(line)

        for x, line in enumerate(text_lines):
            if "dades de la placa" in normalize_text(line):
                properties = []

                properties.extend(separate_columns(text_lines[x+2]))
                properties.extend(separate_columns(text_lines[x+4]))
                properties.extend(separate_columns(text_lines[x+6]))
                properties.extend(separate_columns(text_lines[x+8]))
                
                new_offer = Offer(*properties)
                
                offers.append(new_offer)
    except Exception as e:
        print(f"Error while scrapping PDF: {e}")
    
def scrappe_json(json_string):
    global offers
    try:
        for item in json_string:
            new_offer = Offer(
                identifier=item.get("CODI", None),
                date=item.get("DATA", None),
                speciality=item.get("PERFIL", None),
                application=item.get("INFO_TERMINI", None),
                centerName=item.get("CENTRE") or item.get("CENTRE_ALTRES") or None,
                city="Barcelona",
                startDate=item.get("INCORPORACIO", None)
            )

            offers.append(new_offer)
    except Exception as e:
        print(f"Error while scrapping JSON: {e}")
    
def check_urls():
    try:
        for url in url_array:
            check_url(url)
    except Exception as e:
        print(f"Error checking the URLs: {e}")

def set_configuration():
    global url_array, keywords_array, chat_id_array
    try:
        url_array = URLS.split(';')
        chat_id_array = TELEGRAM_TOKEN_CHAT_IDS.split(';')
        keywords_array = KEYWORDS.split(';')
    except Exception as e:
        print(f"Error setting the configuration: {e}")

def save_message(msg):
    try:
        message_list.append(msg)
    except Exception as e:
        print(f"Error saving the message {msg}: {e}")

def send_notification(msg):
    try:
        if ENV and ENV != "local":
            print(f"Sending notifications through Telegram...")
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
        else:
            print(f"Sending notifications through terminal output...")
            print(f"{msg}")
    except Exception as e:
        print(f"Error sending a notification {msg}: {e}")

def send_telegram_notification(message):
    try:
        for chat_id in chat_id_array:
            requests.post(
                url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                data={"chat_id": chat_id, "text": message, "parse_mode": "HTML"}
            )
    except Exception as e:
        print(f"Error sending Telegram notifications: {e}")

def send_terminal_notification(message):
    try:
        print(f"{message}")
    except Exception as e:
        print(f"Error sending terminal notifications: {e}")

def filter_offers():
    global filtered_offers
    try:
        normalized_keywords = [normalize_text(k) for k in keywords_array]

        filtered_offers = list(filter(lambda o: valid_offer(o, normalized_keywords), offers))
    except Exception as e:
        print(f"Error filtering offers: {e}") 

def valid_offer(offer: Offer, keywords: list[str]) -> bool:
    try:
        if not offer.speciality:
            return False
        
        normalized_speciality = normalize_text(offer.speciality)

        return any(kw.lower() in normalized_speciality for kw in keywords)
    except Exception as e:
        print(f"Error validating offer: {e}") 

def prepare_messages():
    global message_list
    try:
        for offer in filtered_offers:
            parts = [f"🚀 <b>Nueva oferta encontrada</b>\n"]

            message_fields = [
                ("Identificador", offer.identifier),
                ("Fecha publicacion", offer.date),
                ("Especialidad", offer.speciality),
                ("Plazo", offer.application),
                ("Nombre", offer.centerName),
                ("Dirección", offer.address),
                ("Municipio", offer.city),
                ("Teléfono", offer.telephone),
                ("Jornada", offer.time),
                ("Incorporación", offer.startDate),
                ("Fin", offer.endDate)
            ]

            for tag, value in message_fields:
                if value:
                    parts.append(f"<b>{tag}:</b> {value}")

            if(len(parts) > 1):
                final_message = "\n".join(parts)
                message_list.append(final_message)
    except Exception as e:
        print(f"Error preparing the messages: {e}") 

def send_notifications():
    try:
        local = ENV and ENV != "local"

        if(local):
            print(f"Sending notifications through Telegram...")
        else:
            print(f"Sending notifications through terminal output...")

        for message in message_list:
            if local:
                send_telegram_notification(message)
            else:
                send_terminal_notification(message)
    except Exception as e:
        print(f"Error sending the notifications: {e}")

def search_keywords(text):
    clean_text = normalize_text(text)

    found = []

    for keyword in keywords_array:
        clean_keyword = normalize_text(keyword)

        if clean_keyword in clean_text:
            found.append(keyword)
    
    return found

def normalize_text(text):
    if not text:
        return ""
    
    nfd_text = unicodedata.normalize("NFD", text)

    text_without_symbols = "".join(c for c in nfd_text if unicodedata.category(c) != "Mn" or c == '\u0303')

    return text_without_symbols.lower()

def separate_columns(line):
    return [block.strip() for block in re.split(r'\s{2,}', line) if block.strip()]

if __name__ == "__main__":
    try:
        logger = logging.getLogger("pypdf")
        logger.setLevel(logging.ERROR)

        set_configuration()
        check_urls()
        filter_offers()
        prepare_messages()
        send_notifications()
    except Exception as e:
        print(e)