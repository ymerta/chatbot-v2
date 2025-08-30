FROM python:3.11-slim

# Sistem paketleri
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Ortam değişkenleri
ENV DATA_DIR=/data
ENV FAISS_STORE_PATH=/data/embeddings/faiss_store
ENV ENVIRONMENT=production
# FAISS’i Hugging Face Hub’dan alacağız → scrape kapalı
ENV ALLOW_SCRAPE=0
# Hugging Face dataset repo bilgileriniz
ENV HUB_REPO_ID=ymerta/netmerianbot-faiss
ENV HUB_SUBFOLDER=faiss_store
# HF cache’i yazılabilir bir yere yönlendir (/.cache hatasını önler)
ENV HF_HOME=/data/.cache/huggingface
ENV HF_HUB_CACHE=/data/.cache/huggingface/hub
ENV HOME=/root

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

# Kalıcı data ve HF cache klasörlerini oluştur + izin ver
RUN mkdir -p /data/embeddings/faiss_store && \
    mkdir -p /data/.cache/huggingface/hub && \
    chmod -R 777 /data

EXPOSE 7860

# Uygulama başlatma
CMD ["uvicorn", "app_server:app", "--host", "0.0.0.0", "--port", "7860"]
