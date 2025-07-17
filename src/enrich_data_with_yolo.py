import os
import json
import psycopg2
from dotenv import load_dotenv
from ultralytics import YOLO
from PIL import Image
import torch
from ultralytics.nn.tasks import DetectionModel
from torch.nn.modules.container import Sequential
from ultralytics.nn.modules.conv import Conv
from torch.nn.modules.conv import Conv2d
from torch.nn.modules.batchnorm import BatchNorm2d
from torch.nn.modules.activation import SiLU
from ultralytics.nn.modules.block import C2f
from torch.nn.modules.container import ModuleList
from ultralytics.nn.modules.block import Bottleneck
from ultralytics.nn.modules.block import SPPF
from torch.nn.modules.pooling import MaxPool2d
from torch.nn.modules.upsampling import Upsample
from ultralytics.nn.modules.conv import Concat
from ultralytics.nn.modules.head import Detect
from ultralytics.nn.modules.block import DFL

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

MEDIA_DIR = "/app/data/raw/telegram_media"

def create_enriched_schema_and_table(conn):
    with conn.cursor() as cur:
        cur.execute("CREATE SCHEMA IF NOT EXISTS enriched;")
        conn.commit()
        print("Schema 'enriched' ensured.")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS enriched.image_detections (
                detection_id SERIAL PRIMARY KEY,
                message_id BIGINT NOT NULL,
                image_file_path TEXT NOT NULL,
                detected_object TEXT NOT NULL,
                confidence REAL NOT NULL,
                bbox_x_min REAL,
                bbox_y_min REAL,
                bbox_x_max REAL,
                bbox_y_max REAL,
                detection_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
        print("Table 'enriched.image_detections' ensured.")

def enrich_images_with_yolo():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Connected to PostgreSQL database.")

        create_enriched_schema_and_table(conn)

        cur = conn.cursor()

        cur.execute("""
            SELECT message_id, image_file_path
            FROM public.fct_messages
            WHERE has_image = TRUE AND image_file_path IS NOT NULL;
        """)
        messages_with_images = cur.fetchall()
        print(f"Found {len(messages_with_images)} messages with images to process.")

        torch.serialization.add_safe_globals([DetectionModel, Sequential, Conv, Conv2d, BatchNorm2d, SiLU, C2f, ModuleList, Bottleneck, SPPF, MaxPool2d, Upsample, Concat, Detect, DFL])

        model = YOLO('yolov8n.pt')
        print("YOLOv8n model loaded.")

        for message_id, image_file_path in messages_with_images:
            full_image_path = os.path.join(MEDIA_DIR, image_file_path)
            print(f"Processing image for message_id {message_id}: {full_image_path}")

            if not os.path.exists(full_image_path):
                print(f"Warning: Image file not found at {full_image_path}. Skipping.")
                continue

            try:
                image = Image.open(full_image_path)
                
                results = model(image)

                for r in results:
                    boxes = r.boxes
                    for box in boxes:
                        class_id = int(box.cls[0])
                        confidence = float(box.conf[0])
                        detected_object = model.names[class_id]
                        
                        bbox_xyxy = box.xyxy[0].tolist()
                        bbox_x_min, bbox_y_min, bbox_x_max, bbox_y_max = bbox_xyxy[0], bbox_xyxy[1], bbox_xyxy[2], bbox_xyxy[3]

                        cur.execute("""
                            INSERT INTO enriched.image_detections (
                                message_id, image_file_path, detected_object, confidence,
                                bbox_x_min, bbox_y_min, bbox_x_max, bbox_y_max
                            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                        """, (
                            message_id, full_image_path, detected_object, confidence,
                            bbox_x_min, bbox_y_min, bbox_x_max, bbox_y_max
                        ))
                        conn.commit()
                        print(f"  - Detected: {detected_object} (Confidence: {confidence:.2f})")

            except Exception as e:
                print(f"Error processing image {full_image_path} for message {message_id}: {e}")
                conn.rollback()

        print("Image enrichment process completed.")

    except psycopg2.Error as e:
        print(f"Database error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if conn:
            conn.close()
            print("Database connection closed.")

if __name__ == "__main__":
    enrich_images_with_yolo()
