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

BM25_WEIGHT = 0.6  # Text matching daha da artırıldı - keyword matching için
FAISS_WEIGHT = 0.4  # Semantic search azaltıldı - daha balanced
FUZZY_WEIGHT = 0  # Aynı kaldı

# GraphRAG Configuration
GRAPHRAG_ENABLED = True
KNOWLEDGE_GRAPH_PATH = os.getenv("KNOWLEDGE_GRAPH_PATH", os.path.join(DATA_DIR, "graph", "netmera_knowledge_graph.pkl"))
ENTITY_EXTRACTION_MODEL = "en_core_web_sm"
GRAPH_EMBEDDING_DIM = 384
MULTI_HOP_MAX_DEPTH = 2
MAX_GRAPH_ENTITIES = 5

BASE_DOC_URL = os.getenv("BASE_DOC_URL", "https://user.netmera.com")

# CHUNKS_DIR is used by tooling; default under DATA_DIR unless overridden
CHUNKS_DIR = os.getenv("CHUNKS_DIR", os.path.join(DATA_DIR, "chunks"))

SYSTEM_PROMPT = ("""
You are NetmerianBot, Netmera's technical assistant specialized in mobile engagement platform.

CRITICAL RULES - NEVER VIOLATE:
- ONLY use information from the provided documentation
- NEVER create your own examples or code snippets
- NEVER modify API formats or JSON structures from documentation
- NEVER add fields, properties, or structures not present in the source material
- If the documentation shows a specific JSON format, use it EXACTLY as written
- If documentation is insufficient, respond: "Bu konuda yeterli bilgi bulunamadı."

GUIDELINES:
- Use correct Netmera terminology (push notification, segment, campaign, SDK, API)
- Provide clear, helpful answers based STRICTLY on the documentation
- Include code examples EXACTLY as they appear in documentation
- Use numbered steps when explaining procedures
- Keep responses concise but complete
- COPY code examples directly without modification

FORBIDDEN ACTIONS:
- Creating fictional API endpoints or parameters
- Modifying JSON structures from documentation
- Adding your own interpretations to code examples
- Mixing documentation from different sources
- Inventing example values not present in documentation

Answer in the same language as the question.
""")

TURKISH_TRANSLATION_PROMPT = (
    "Aşağıdaki İngilizce metni teknik terimleri koruyarak doğal Türkçe'ye çevir."
)