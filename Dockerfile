FROM python:3.11-slim

# Sistem paketleri
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ortam değişkenleri
ENV DATA_DIR=/data
ENV FAISS_STORE_PATH=/data/embeddings/faiss_store
ENV ENVIRONMENT=production
# Artık FAISS’i Hugging Face Hub’dan çekeceğiz → scrape kapalı
ENV ALLOW_SCRAPE=0
# Hugging Face dataset repo bilgileriniz
ENV HUB_REPO_ID=ymerta/netmerianbot-faiss
ENV HUB_SUBFOLDER=faiss_store
# Eğer dataset private ise HF_TOKEN secret’ını container’a inject etmen lazım (Space’de Settings → Secrets)

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Uygulama dosyaları
COPY src ./src
COPY app_server.py .

# Sabit data dosyaları (FAQ vb.)
RUN mkdir -p ./data
COPY data/faq_answers.json ./data/faq_answers.json

# data klasörünü kopyalıyoruz (FAISS dosyaları dahil olmayabilir ama sorun değil)
COPY data ./data

# Kalıcı data klasörü oluştur
RUN mkdir -p /data && chmod -R 777 /data

EXPOSE 7860

# Uygulama başlatma
CMD ["uvicorn", "app_server:app", "--host", "0.0.0.0", "--port", "7860"]
