import requests
import io
import os
import json
import unicodedata
from pypdf import PdfReader
from bs4 import BeautifulSoup
from dotenv import load_dotenv

load_dotenv()

# Configuración
TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
URLS = os.getenv('URLS')
KEYWORDS = os.getenv('KEYWORDS')
ENV = os.getenv('ENV')

url_array = []
keywords_array = []
message_list = []

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
        elif "text/html" in content_type:
            scrappe_html(response.text)
        elif "application/json" in content_type:
            scrappe_json(response.json())
        else:
            print(f"Content-type not recognised: {content_type}")
                
    except Exception as e:
        print(f"Error while scrapping content: {e}")

def scrappe_pdf(content):
    try:
        with io.BytesIO(content) as f:
            reader = PdfReader(f)
            text = "".join(page.extract_text() for page in reader.pages).lower()
            
            found_keywords = search_keywords(text)

            if found_keywords:
                print(f"Found entry while scrapping PDF")
                message = f"🎯 Found! The PDF contains: {', '.join(found_keywords)}"
                save_message(message)
    except Exception as e:
        print(f"Error while scrapping PDF: {e}")


def scrappe_html(content):
    try:
        soup = BeautifulSoup(content, 'html.parser')
        
        body = soup.find("body")

        if body:
            for trash in body(["script", "style", "nav", "footer", "header"]):
                trash.decompose()

            text = body.get_text()

            found_keywords = search_keywords(text)

            if found_keywords:
                print(f"Found entry while scrapping HTML")
                message = f"🎯 Found! The HTML contains:: {', '.join(found_keywords)}"
                save_message(message)
    except Exception as e:
        print(f"Error while scrapping HTML: {e}")
    
def scrappe_json(content):
    try:
        text = json.dumps(content, ensure_ascii=False)

        found_keywords = search_keywords(text)

        if found_keywords:
            print(f"Found entry while scrapping JSON")
            message = f"🎯 Found! The JSON contains:: {', '.join(found_keywords)}"
            save_message(message)
    except Exception as e:
        print(f"Error while scrapping JSON: {e}")
    
def check_urls():
    try:
        for url in url_array:
            check_url(url)
    except Exception as e:
        print(f"Error checking the URLs: {e}")

def set_configuration():
    global url_array, keywords_array
    try:
        url_array = URLS.split(';')
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

def send_telegram_notifications():
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

        for message in message_list:
            requests.post(url, data={"chat_id": CHAT_ID, "text": message})
    except Exception as e:
        print(f"Error sending Telegram notifications: {e}")

def send_terminal_notifications():
    try:
        for message in message_list:
            print(f"{message}")
    except Exception as e:
        print(f"Error sending terminal notifications: {e}")

def send_notifications():
    try:
        if ENV and ENV != "local":
            print(f"Sending notifications through Telegram...")
            send_telegram_notifications()
        else:
            print(f"Sending notifications through terminal output...")
            send_terminal_notifications()
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

if __name__ == "__main__":
    try:
        set_configuration()
        check_urls()
        send_notifications()
    except Exception as e:
        print(e)