# 1. Base image pakai Python 3.11
FROM python:3.11-slim

# 2. Set folder kerja di container
WORKDIR /app

# 3. Install dependencies sistem untuk beberapa package
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libffi-dev libssl-dev git curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Copy requirements.txt lalu install semua Python package
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# 5. Copy seluruh kode aplikasi ke container
COPY . .

# 6. Buka port default Dash
EXPOSE 8050

# 7. Jalankan app menggunakan gunicorn (production-ready)
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:8050"]
