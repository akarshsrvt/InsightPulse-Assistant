FROM python:3.11-slim-bookworm

# Install system dependencies required for scientific libraries and general operations
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements.txt first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application files and dataset folders
COPY chatbot/ ./chatbot/
COPY Data/ ./Data/

# Expose Streamlit's default port
EXPOSE 8501

# Configure Streamlit behavior using environment variables
ENV STREAMLIT_SERVER_PORT=8501
ENV STREAMLIT_SERVER_ADDRESS=0.0.0.0
ENV STREAMLIT_SERVER_HEADLESS=true
ENV PYTHONUNBUFFERED=1

# Command to run the application
CMD ["streamlit", "run", "chatbot/app.py"]