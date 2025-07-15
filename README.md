Telegram Data Product
This repository contains the code and infrastructure for a data product designed to extract, transform, enrich, and analyze data from Telegram channels.

Project Overview
This project aims to build an end-to-end data pipeline that can:

Extract messages from specified Telegram channels.

Load raw data into a PostgreSQL database.

Transform raw data into clean, structured, and analytical models using dbt.

Enrich messages with additional insights (e.g., image content analysis using YOLO).

Serve processed data via a FastAPI application.

Orchestrate the entire pipeline using Dagster.

Current Status (Interim Submission)
As of the interim submission, the following components have been set up and implemented:

Task 0: Project Setup & Environment Management (Complete)
Dockerized Environment: The project leverages Docker Compose to containerize all services (Python application, PostgreSQL database), ensuring a consistent and isolated development environment.

Environment Variable Management: Sensitive credentials and configurations are securely managed using a .env file, following best practices.

Version Control: The project is fully version-controlled with Git and hosted on GitHub.

Secure Credential Handling: A .gitignore file is properly configured to prevent sensitive files (like .env and Telethon session files) from being committed.

Organized Structure: The codebase follows a clear directory structure (src/, data/, etc.).

Task 1: Data Scraping & Collection (Extract & Load to Raw Files)
Extract (Scraping Logic): The Python scraper (src/scrape_telegram.py) is fully implemented. It connects to Telegram, authenticates, resolves channel entities (by username or ID), and extracts message details.

Load (to Raw Files): The scraper includes logic to save extracted messages as JSON files in the data/raw/ directory.

Current Challenge: Telegram API Blocking
During testing, we've encountered persistent blocking by Telegram's API, preventing live data acquisition. This appears to be a security measure from Telegram's side, possibly due to repeated connection attempts or IP flagging.

Mitigation Strategy for Continuity:
To ensure progress on downstream tasks, we will use manually created sample JSON data in the data/raw/ directory. This allows us to develop and test the data loading, transformation, enrichment, and serving layers of the pipeline.

Getting Started (Local Development)
Prerequisites
Docker Desktop (or Docker Engine & Docker Compose)

Git

Setup Instructions
Clone the Repository:

git clone https://github.com/Ybtry/Telegram_Data_Product.git
cd Telegram_Data_Product

Create .env File:
Create a file named .env in the root of your project directory (Telegram_Data_Product/). Populate it with your Telegram API credentials and database connection details. Do NOT commit this file to Git.

# Telegram API Credentials (Obtain from https://my.telegram.org/)
TELEGRAM_API_ID=YOUR_API_ID
TELEGRAM_API_HASH=YOUR_API_HASH
TELEGRAM_PHONE_NUMBER=+YOUR_PHONE_NUMBER # e.g., +251912345678

# Telegram Channel Configuration
TELEGRAM_CHANNEL_USERNAME=-1001666492664 # Example: Use the numerical ID from @JsonDumpBot or a public username (e.g., @telegram)
TELEGRAM_MESSAGE_LIMIT=50 # Number of messages to scrape

# PostgreSQL Database Credentials (for Docker service)
DB_USER=postgres
DB_PASSWORD=mySecurePassword123
DB_NAME=telegram_data_warehouse
DB_HOST=db # This refers to the 'db' service name in docker-compose
DB_PORT=5432

# Other environment variables (if any)
TEST_VAR=hello

Build and Start Docker Services:
From the project root directory, build and start your Docker containers.

docker-compose up --build -d

This will build the app image (containing your Python scraper) and start the db (PostgreSQL) service.

Verify Docker Services:
Check if your containers are running:

docker-compose ps

You should see app and db services listed as Up.

Running the Telegram Scraper (Attempt)
To run the scraper from within the Docker container:

Execute the scraper script:

docker-compose exec app python src/scrape_telegram.py

First Run: You will be prompted to enter a Telegram authentication code (sent to your TELEGRAM_PHONE_NUMBER).

Subsequent Runs: If successful, a session file (anon.session) will be created in your project root, allowing future runs to bypass the login prompt.

Note on API Blocking: As mentioned, live scraping may fail due to Telegram's API blocking. The logs will indicate if an entity cannot be resolved.

Preparing Sample Data for Downstream Tasks
Since live scraping is currently blocked, you can manually create sample JSON files to proceed with data loading and transformation:

Create data/raw/ directory (if it doesn't exist):

mkdir -p data/raw

Create sample JSON files:
Inside data/raw/, create files like lobelia4cosmetics_messages.json (or any other channel names you plan to process). Ensure the structure matches what your scrape_telegram.py would output.

Example data/raw/lobelia4cosmetics_messages.json content:

[
    {
        "id": 1,
        "date": "2024-07-10T10:00:00",
        "message": "Special offer on Painkillers! Buy 2, get 1 free. #pharma #offer",
        "sender_id": 12345,
        "peer_id": -1001666492664,
        "views": 250,
        "forwards": 15,
        "replies": 3,
        "post_author": "Pharma Admin",
        "grouped_id": null,
        "url": "https://t.me/c/1666492664/1"
    },
    {
        "id": 2,
        "date": "2024-07-11T14:30:00",
        "message": "New cosmetic arrivals this week! Check out our new line of skin care products.",
        "sender_id": 67890,
        "peer_id": -1001666492664,
        "views": 180,
        "forwards": 8,
        "replies": 0,
        "post_author": "Cosmetics Team",
        "grouped_id": null,
        "url": "https://t.me/c/1666492664/2"
    }
]

Add more messages and channels as needed to represent your expected data.
