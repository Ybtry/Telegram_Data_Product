# Use a slim Python base image for smaller size
FROM python:3.12-slim-bookworm

# Add a dummy argument to bust the cache for the apt-get install layer
ARG CACHE_BUST_APT=1

# Install system dependencies required for Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    git \
    libgl1-mesa-glx \
    libxext6 \
    libsm6 \
    libxrender1 \
    libglib2.0-0

# Clean up apt caches to reduce image size - MOVED TO SEPARATE RUN INSTRUCTION
RUN rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Dynamically create requirements.txt inside the Dockerfile using a 'here document'
# This ensures the content is exactly as expected and bypasses any COPY issues.
RUN cat << EOF > requirements.txt
python-dotenv==1.1.1
telethon==1.32.0
dbt-core==1.8.0
dbt-postgres==1.8.0
# dbt-utils # Completely removed due to persistent installation issues
ultralytics==8.2.3
torch==2.7.0+cpu
torchvision==0.22.0+cpu
Pillow==10.3.0
fastapi==0.111.0
uvicorn==0.29.0
pydantic==2.7.4
dagster==1.8.10
dagster-webserver==1.8.10
dagster-graphql==1.8.10
numpy==1.26.4
psycopg2-binary==2.9.9
EOF

# Upgrade pip before installing other dependencies
RUN pip install --upgrade pip

# Install Python dependencies from the dynamically created requirements.txt
RUN pip install --no-cache-dir -r requirements.txt --extra-index-url https://download.pytorch.org/whl/cpu

# Create the .dbt directory and profiles.yml directly in the container
RUN mkdir -p /root/.dbt && \
    cat << EOT > /root/.dbt/profiles.yml
telegram_data_product:
  target: dev
  outputs:
    dev:
      type: postgres
      host: db
      port: 5432
      user: postgres
      password: mySecurePassword123
      dbname: telegram_data_warehouse
      schema: public
      threads: 1
EOT

# Copy dbt_project.yml from the build context (your local project root) to /app
COPY dbt_project.yml /app/dbt_project.yml

# Set PYTHONUNBUFFERED for better logging in Docker (optional but good practice)
ENV PYTHONUNBUFFERED=1

# Set PYTHONPATH to include the directory where your actual source code will reside.
ENV PYTHONPATH=/app/src

# Expose ports for FastAPI (8000) and Dagster UI (3000)
EXPOSE 8000
EXPOSE 3000

# Default command for the container (keeps it running indefinitely for development)
CMD ["tail", "-F", "/dev/null"]
