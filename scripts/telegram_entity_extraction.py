# telegram_entity_extraction.py

import os
import re
import json
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.tl.types import MessageMediaPhoto

# Load from .env or hardcode
API_ID = '*********'
API_HASH = '***********'

# Telegram channels to crawl
CHANNELS = [
    'ZemenExpress', 'nevacomputer', 'meneshayeofficial', 'ethio_brand_collection',
    'Leyueqa', 'sinayelj', 'Shewabrand', 'helloomarketethiopia', 'modernshoppingcenter',
    'qnashcom', 'Fashiontera', 'kuruwear', 'gebeyaadama', 'MerttEka', 'forfreemarket',
    'classybrands', 'marakibrand', 'aradabrand2', 'marakisat2', 'belaclassic', 'AwasMart'
]

RAW_DIR = 'data/raw'
PROCESSED_DIR = 'data/processed'
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

# Utility: Amharic-aware text cleaner
def preprocess_amharic_text(text):
    text = text.lower()
    text = re.sub(r'[፣፡።]', ' ', text)
    text = re.sub(r'[\n\r]+', ' ', text)
    text = re.sub(r'["“”\'\'.,!?()\[\]{}<>/@#$%^&*_+=\\|-]', '', text)
    return text.strip()

# Utility: Simple Entity Extractor (product, price, phone)
def extract_entities(text):
    entities = {
        "price": re.findall(r'[0-9]{2,}\s?(birr|ብር)', text, re.IGNORECASE),
        "phones": re.findall(r'(\+251|0)?9[0-9]{8}', text),
        "products": re.findall(r'(ነዶ|ጫማ|ቦታ|ሸማኔ|ሱሪ|ቀሚስ|ቤት|የ[\w\s]+እቃ)', text)
    }
    return entities

# Main async client logic
client = TelegramClient('crawler_session', API_ID, API_HASH)

async def crawl_and_process():
    await client.start()
    for channel in CHANNELS[:5]:  # At least 5 for fine-tuning
        try:
            entity = await client.get_entity(f'https://t.me/{channel}')
            raw_messages = []
            structured = []

            async for message in client.iter_messages(entity, limit=100):
                if not message.text:
                    continue
                cleaned = preprocess_amharic_text(message.text)
                entities = extract_entities(cleaned)
                
                record = {
                    "channel": channel,
                    "timestamp": message.date.isoformat(),
                    "text": cleaned,
                    "raw_text": message.text,
                    "sender_id": getattr(message.sender_id, 'user_id', None),
                    "entities": entities
                }

                raw_messages.append(record)
                structured.append(record)

            # Save raw + processed
            with open(f'{RAW_DIR}/{channel}.json', 'w', encoding='utf-8') as f:
                json.dump(raw_messages, f, ensure_ascii=False, indent=2)

            with open(f'{PROCESSED_DIR}/{channel}_structured.json', 'w', encoding='utf-8') as f:
                json.dump(structured, f, ensure_ascii=False, indent=2)

            print(f"[✔] Crawled and processed: @{channel} ({len(raw_messages)} messages)")

        except Exception as e:
            print(f"[✘] Failed @{channel}: {e}")

with client:
    client.loop.run_until_complete(crawl_and_process())
