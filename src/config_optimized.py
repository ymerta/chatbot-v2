import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Base directory - proje kök klasörü
BASE_DIR = Path(__file__).parent.parent

# Windows/Unix uyumlu data directory
if os.getenv("ENVIRONMENT") == "production":
    DATA_DIR = os.getenv("DATA_DIR", "/data")
else:
    DATA_DIR = os.getenv("DATA_DIR", str(BASE_DIR / "data"))

# FAISS index klasörü
FAISS_STORE_PATH = os.getenv("FAISS_STORE_PATH", os.path.join(DATA_DIR, "embeddings", "faiss_store"))

# Debug bilgileri
print(f"BASE_DIR: {BASE_DIR}")
print(f"DATA_DIR: {DATA_DIR}")
print(f"FAISS_STORE_PATH: {FAISS_STORE_PATH}")
print(f"FAISS path exists: {Path(FAISS_STORE_PATH).exists()}")

CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")

# 🔧 OPTIMIZED RETRIEVAL WEIGHTS
BM25_WEIGHT = 0.6   # Text matching artırıldı (0.5 -> 0.6)
FAISS_WEIGHT = 0.4  # Semantic search azaltıldı (0.5 -> 0.4)
FUZZY_WEIGHT = 0    # Devre dışı

# 🎯 RETRIEVAL OPTIMIZATION SETTINGS
RETRIEVAL_K = 10           # Daha fazla sonuç getir (6 -> 10)
MIN_SIMILARITY_THRESHOLD = 0.2  # Daha düşük threshold (default: 0.5)
CONFIDENCE_THRESHOLD = 0.15      # Confidence threshold (line 88'deki divisor için)

BASE_DOC_URL = os.getenv("BASE_DOC_URL", "https://user.netmera.com")

# CHUNKS_DIR is used by tooling
CHUNKS_DIR = os.getenv("CHUNKS_DIR", os.path.join(DATA_DIR, "chunks"))

# 🔧 ENHANCED SYSTEM PROMPT
SYSTEM_PROMPT = ("""
You are NetmerianBot, Netmera's technical assistant specialized in mobile engagement platform.

GUIDELINES:
- Use correct Netmera terminology (push notification, segment, campaign, SDK, API)
- For procedural questions ("how to", "nasıl"): provide numbered steps
- For informational questions ("what is", "nedir"): provide natural explanations  
- Include code examples when relevant
- Keep responses concise and direct
- If documentation is limited, provide general guidance based on Netmera platform knowledge

RESPONSE STRATEGY:
- If exact info not found: provide related information from available docs
- For error handling: suggest general troubleshooting steps
- For technical issues: mention checking logs, configuration, or contacting support

Use the provided documentation as primary source. If insufficient: provide helpful general guidance.

Answer in the same language as the question.
""")

# 🔧 ENHANCED QUERY PREPROCESSING
TURKISH_TECHNICAL_TERMS = {
    # Error handling terms
    "hata": ["error", "issue", "problem", "fail"],
    "sorun": ["problem", "issue", "trouble"],
    "limit": ["limit", "size", "payload", "quota"],
    "boyut": ["size", "payload", "limit"],
    "engel": ["block", "blocked", "restrict"],
    "yasaklı": ["blocked", "banned", "restricted"],
    
    # Network terms  
    "ip": ["ip address", "network", "connection"],
    "adres": ["address", "url", "endpoint"],
    "bağlantı": ["connection", "network", "connectivity"],
    
    # Technical terms
    "entegrasyon": ["integration", "integrate", "setup"],
    "modül": ["module", "component", "feature"],
    "yapılandırma": ["configuration", "config", "setup"],
    "kurulum": ["installation", "setup", "install"],
    
    # Email terms
    "e-posta": ["email", "mail", "message"],
    "teslimat": ["delivery", "send", "dispatch"]
}

# Query expansion mapping
QUERY_EXPANSIONS = {
    "push notification": ["push message", "notification", "alert", "messaging"],
    "email": ["e-mail", "electronic mail", "messaging"],
    "integration": ["entegrasyon", "setup", "configuration"],
    "api": ["rest api", "web api", "service", "endpoint"],
    "sdk": ["software development kit", "library", "framework"],
    "error": ["hata", "sorun", "problem", "issue"],
    "block": ["engel", "restrict", "ban"],
    "delivery": ["teslimat", "send", "dispatch"]
}

TURKISH_TRANSLATION_PROMPT = (
    "Aşağıdaki İngilizce metni teknik terimleri koruyarak doğal Türkçe'ye çevir."
)
