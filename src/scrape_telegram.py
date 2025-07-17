import os
import asyncio
import json
from telethon.sync import TelegramClient
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Channel, PeerChannel 

# --- Configuration from .env ---
API_ID = os.getenv('TELEGRAM_API_ID')
API_HASH = os.getenv('TELEGRAM_API_HASH')
PHONE_NUMBER = os.getenv('TELEGRAM_PHONE_NUMBER')
CHANNEL_USERNAME = os.getenv('TELEGRAM_CHANNEL_USERNAME') 
MESSAGE_LIMIT = int(os.getenv('TELEGRAM_MESSAGE_LIMIT', 50))

# --- File Paths ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data')
RAW_DATA_DIR = os.path.join(DATA_DIR, 'raw')

os.makedirs(RAW_DATA_DIR, exist_ok=True)

# --- Scraper Function ---
async def scrape_channel_messages():
    if not API_ID or not API_HASH:
        print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in the .env file.")
        return

    client = TelegramClient('anon', API_ID, API_HASH)

    print("Connecting to Telegram...")
    try:
        await client.start(phone=PHONE_NUMBER)
        print("Connected to Telegram.")
    except Exception as e:
        print(f"Error connecting to Telegram: {e}")
        print("Please ensure your TELEGRAM_PHONE_NUMBER is correct in .env and follow any prompts.")
        return

    try:
       
        # This helps Telethon build its internal cache of entities the user has access to
        print("Loading user dialogs to build entity cache...")
        await client.get_dialogs() # This helps populate the entity cache

       
        is_numerical_id = False
        try:
            int_channel_id = int(CHANNEL_USERNAME)
            if str(int_channel_id).startswith('-100'): # Check if it's a channel ID format
                is_numerical_id = True
        except ValueError:
            pass # Not an integer, so it must be a username string

        if is_numerical_id:
            print(f"Attempting to resolve channel by numerical ID: {CHANNEL_USERNAME}")
            entity = await client.get_entity(int_channel_id) # Pass the full -100... ID
        else:
            print(f"Attempting to resolve channel by username: {CHANNEL_USERNAME}")
            entity = await client.get_entity(CHANNEL_USERNAME)

        if isinstance(entity, Channel):
            messages_data = []
            print(f"Scraping up to {MESSAGE_LIMIT} messages from '{entity.title}' (ID: {entity.id})...")
            async for message in client.iter_messages(entity, limit=MESSAGE_LIMIT):
                message_dict = {
                    'id': message.id,
                    'date': message.date.isoformat() if message.date else None,
                    'message': message.message,
                    'sender_id': message.sender_id,
                    'peer_id': message.peer_id.channel_id if message.peer_id else None,
                    'views': message.views,
                    'forwards': message.forwards,
                    'replies': message.replies.replies if message.replies else None,
                    'post_author': message.post_author,
                    'grouped_id': message.grouped_id,
                    'url': f"https://t.me/{entity.username}/{message.id}" if entity.username else f"https://t.me/c/{abs(entity.id)}/{message.id}",
                }
                messages_data.append(message_dict)

            print(f"Scraped {len(messages_data)} messages.")

            output_filename_base = entity.username if entity.username else str(abs(entity.id))
            output_filename = f"{output_filename_base}_messages.json"
            output_filepath = os.path.join(RAW_DATA_DIR, output_filename)

            with open(output_filepath, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, ensure_ascii=False, indent=4)

            print(f"Data saved to {output_filepath}")

        else:
            print(f"Error: '{CHANNEL_USERNAME}' resolved to an entity that is not a Channel (Type: {type(entity).__name__}).")
            print("Please ensure you're providing a valid public channel username or its numerical ID.")

    except Exception as e:
        print(f"An unexpected error occurred during scraping: {e}")
        # Add more specific error handling here if common errors persist, e.g., NotAuthorizedError, ChannelPrivateError
    finally:
        print("Disconnecting from Telegram.")
        await client.disconnect()

# --- Main execution ---
if __name__ == '__main__':
    asyncio.run(scrape_channel_messages())