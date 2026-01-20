FROM python:3.9-slim

WORKDIR /app

# Hapus bagian apt-get install gcc yang berat itu.
# Kita kembali ke versi simple.

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]