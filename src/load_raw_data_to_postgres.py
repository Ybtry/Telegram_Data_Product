import os
import json
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
import glob # To find all JSON files

# Load environment variables from .env file
load_dotenv()

# Database connection details from .env
DB_HOST = os.getenv('DB_HOST')
DB_NAME = os.getenv('DB_NAME')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_PORT = os.getenv('DB_PORT')

# Define paths relative to the script's location inside the Docker container
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Point to the base directory for telegram messages, which is now nested
TELEGRAM_MESSAGES_RAW_DIR = os.path.join(os.path.dirname(BASE_DIR), 'data', 'raw', 'telegram_messages')

# Table to store raw Telegram messages
RAW_TABLE_NAME = "telegram_messages"
RAW_SCHEMA_NAME = "raw"

def create_raw_table_and_schema(cursor):
    """
    Creates the raw schema and the raw_telegram_messages table if they don't exist.
    The table stores entire message objects as JSONB and tracks their source file.
    """
    try:
        cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {};").format(
            sql.Identifier(RAW_SCHEMA_NAME)
        ))
        print(f"Schema '{RAW_SCHEMA_NAME}' ensured.")

        # Create table with a JSONB column to store the entire message object
        # We also add a primary key and a source_file column for tracking
        cursor.execute(sql.SQL("""
            CREATE TABLE IF NOT EXISTS {}.{} (
                id SERIAL PRIMARY KEY,
                message_data JSONB NOT NULL,
                source_file VARCHAR(255) NOT NULL, -- Stores the relative path of the source JSON file
                loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """).format(
            sql.Identifier(RAW_SCHEMA_NAME),
            sql.Identifier(RAW_TABLE_NAME)
        ))
        print(f"Table '{RAW_SCHEMA_NAME}.{RAW_TABLE_NAME}' ensured.")
        
    except psycopg2.Error as e:
        print(f"Error creating schema or table: {e}")
        raise # Re-raise to stop execution if table/schema creation fails

def load_json_to_postgres():
    """
    Loads all JSON files from the data/raw/telegram_messages directory (and its
    subdirectories) into the raw PostgreSQL table.
    """
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        conn.autocommit = True # Auto-commit changes for simplicity in this loader

        cursor = conn.cursor()

        # 1. Create schema and table if they don't exist
        create_raw_table_and_schema(cursor)

        # ADDED: Truncate the table before loading new data to ensure a clean slate
        cursor.execute(sql.SQL("TRUNCATE TABLE {}.{} RESTART IDENTITY;").format(
            sql.Identifier(RAW_SCHEMA_NAME),
            sql.Identifier(RAW_TABLE_NAME)
        ))
        print(f"Table '{RAW_SCHEMA_NAME}.{RAW_TABLE_NAME}' truncated.")

        # 2. Find all JSON files in the raw data directory recursively
        # The '**' pattern allows searching in subdirectories
        json_files = glob.glob(os.path.join(TELEGRAM_MESSAGES_RAW_DIR, '**', '*.json'), recursive=True)
        
        if not json_files:
            print(f"No JSON files found in {TELEGRAM_MESSAGES_RAW_DIR} or its subdirectories.")
            print("Please ensure your scraped data (JSONs) are placed in this structure: data/raw/telegram_messages/YYYY-MM-DD/channel_name.json")
            return

        print(f"Found {len(json_files)} JSON files to load.")

        # 3. Load each JSON file
        for file_path in json_files:
            # Get the path relative to 'data/raw/' for the source_file column
            # This makes the source_file column more descriptive and consistent
            relative_file_path = os.path.relpath(file_path, os.path.join(os.path.dirname(BASE_DIR), 'data', 'raw'))
            
            print(f"Processing file: {relative_file_path}")

            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    messages = json.load(f)

                if not isinstance(messages, list):
                    print(f"Warning: File {relative_file_path} does not contain a JSON array. Skipping.")
                    continue

                # Insert each message as a JSONB object
                for message in messages:
                    # Convert Python dict to JSON string for the JSONB column
                    message_json_string = json.dumps(message, ensure_ascii=False)
                    
                    insert_query = sql.SQL("""
                        INSERT INTO {}.{} (message_data, source_file)
                        VALUES (%s, %s);
                    """).format(
                        sql.Identifier(RAW_SCHEMA_NAME),
                        sql.Identifier(RAW_TABLE_NAME)
                    )
                    cursor.execute(insert_query, (message_json_string, relative_file_path))
                print(f"Successfully loaded {len(messages)} messages from {relative_file_path}.")

            except json.JSONDecodeError as e:
                print(f"Error decoding JSON from {relative_file_path}: {e}. Skipping file.")
            except Exception as e:
                print(f"Error loading data from {relative_file_path} to PostgreSQL: {e}")

    except psycopg2.Error as e:
        print(f"Database connection or operation error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == '__main__':
    load_json_to_postgres()
