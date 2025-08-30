import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directory - proje kök klasörü
BASE_DIR = Path(__file__).parent.parent

# Windows/Unix uyumlu data directory
# Production'da (HF Spaces) /data kullan, local'de proje içi data klasörü
if os.getenv("ENVIRONMENT") == "production":
    DATA_DIR = os.getenv("DATA_DIR", "/data")
else:
    # Local development - proje içindeki data klasörünü kullan
    DATA_DIR = os.getenv("DATA_DIR", str(BASE_DIR / "data"))

# FAISS index klasörü (tam klasör yolu)
FAISS_STORE_PATH = os.getenv("FAISS_STORE_PATH", os.path.join(DATA_DIR, "embeddings", "faiss_store"))

# Debug bilgileri
print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"FAISS_STORE_PATH: {FAISS_STORE_PATH}")
print(f"FAISS path exists: {Path(FAISS_STORE_PATH).exists()}")

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

BM25_WEIGHT = 0.3
FAISS_WEIGHT = 0.5
FUZZY_WEIGHT = 0.2

BASE_DOC_URL = os.getenv("BASE_DOC_URL", "https://user.netmera.com")
FAQ_URL = os.getenv("FAQ_URL", "https://user.netmera.com/netmera-user-guide/beginners-guide-to-netmera/faqs")

# CHUNKS_DIR is used by tooling; default under DATA_DIR unless overridden
CHUNKS_DIR = os.getenv("CHUNKS_DIR", os.path.join(DATA_DIR, "chunks"))

SYSTEM_PROMPT = ("""
You are NetmerianBot, a knowledgeable assistant specialized in Netmera's features and documentation.

Your job is to answer the user's question using only the provided content. If the content contains relevant information, provide a clear, concise answer.

Guidelines:
- Use only the content below.
- Do not mention training data or your knowledge cut-off.
- Rephrase and summarize naturally.
- If the content does not answer the question, respond with: "There is no relevant information available."
""")

TURKISH_TRANSLATION_PROMPT = (
    "Aşağıdaki İngilizce metni teknik terimleri koruyarak doğal Türkçe'ye çevir."
)