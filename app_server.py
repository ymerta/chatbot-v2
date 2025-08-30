# app_server.py
import os
from pathlib import Path
import shutil
from typing import List
import logging

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from src.graph.app_graph import build_app_graph
from src.config import FAISS_STORE_PATH
from src.index_build import main as build_index
from huggingface_hub import hf_hub_download

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI(title="NetmerianBot API")

class ChatIn(BaseModel):
    query: str

class ChatOut(BaseModel):
    answer: str
    citations: List[str] = []
    suggestions: List[str] = []

def ensure_openai_key():
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError(
            "OPENAI_API_KEY bulunamadı. HF Spaces → Settings → Secrets altına ekleyin."
        )

def try_download_faiss_from_hub(target_dir: Path) -> bool:
    """
    Hugging Face Dataset reposundan index dosyalarını indirir.
    Gerekli env'ler:
      - HUB_REPO_ID (örn: 'ymerta/netmerianbot-faiss')
      - HUB_SUBFOLDER (default: 'faiss_store')
      - HUB_REVISION (opsiyonel: tag/sha)
      - HF_HOME / HF_HUB_CACHE (opsiyonel, cache kökleri)
    """
    repo_id = os.getenv("HUB_REPO_ID")
    subfolder = os.getenv("HUB_SUBFOLDER", "faiss_store")
    revision = os.getenv("HUB_REVISION")  # optional

    if not repo_id:
        logger.info("HUB_REPO_ID tanımlı değil; Hub indirme adımı atlanıyor.")
        return False

    # HF cache konumunu yazılabilir bir dizine al (Dockerfile'da /data/.cache/... set edildi)
    cache_root = Path(os.getenv("HF_HUB_CACHE") or os.getenv("HF_HOME") or "/data/.cache/huggingface/hub")
    try:
        cache_root.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        logger.warning(f"Cache klasörü oluşturulamadı ({cache_root}): {e}")

    logger.info(
        f"Hugging Face Hub'dan indirme denemesi: "
        f"repo_id={repo_id}, subfolder={subfolder}, revision={revision or '(default)'} "
        f"cache_root={cache_root}"
    )

    target_dir.mkdir(parents=True, exist_ok=True)
    want_files = ["index.faiss", "index.pkl"]
    ok = True
    for fname in want_files:
        try:
            fpath = hf_hub_download(
                repo_id=repo_id,
                filename=f"{subfolder}/{fname}",
                repo_type="dataset",
                revision=revision,
                # cache'i açıkça ver → /.cache izin hatasını önler
                local_dir=str(cache_root),
                local_dir_use_symlinks=False,  # symlink yerine kopya
            )
            shutil.copy2(fpath, target_dir / fname)
            logger.info(f"Hub'dan indirildi: {fname}")
        except Exception as e:
            logger.error(f"Hub indirme başarısız: {fname}: {e}")
            ok = False
    return ok

def load_or_build_faiss():
    """
    Yükleme stratejisi:
      1) Hedef konumda FAISS varsa doğrudan yükle.
      2) Repo içindeki data/embeddings/faiss_store'tan kopyalamayı dene.
      3) Hugging Face Hub (dataset) üzerinden indirmeyi dene.
      4) ALLOW_SCRAPE=1 ise runtime'da indexi üret.
      5) Aksi halde hata ver.
    """
    store_path = Path(FAISS_STORE_PATH)
    logger.info(f"FAISS store path: {store_path}")

    # 1) Local hedefte varsa yükle
    if store_path.exists() and (store_path / "index.faiss").exists():
        logger.info("Hedef konumda FAISS index bulundu, yükleniyor...")
        try:
            ensure_openai_key()
            emb = OpenAIEmbeddings()
            vs = FAISS.load_local(str(store_path), emb, allow_dangerous_deserialization=True)
            logger.info("FAISS index başarıyla yüklendi.")
            return vs
        except Exception as load_err:
            logger.error(f"Mevcut FAISS yüklenemedi, fallback denenecek: {load_err}")

    # 2) Repo data dizininden kopyalamayı dene (geliştirici modu için)
    repo_faiss_path = Path("data/embeddings/faiss_store")
    logger.info(f"Repo FAISS yolu kontrol ediliyor: {repo_faiss_path}")
    if repo_faiss_path.exists() and (repo_faiss_path / "index.faiss").exists():
        logger.info(f"Repo içinde FAISS bulundu, {store_path} konumuna kopyalanıyor...")
        try:
            store_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(repo_faiss_path, store_path, dirs_exist_ok=True)

            if (store_path / "index.faiss").exists():
                logger.info("Repo'dan kopyalama başarılı, FAISS yükleniyor...")
                ensure_openai_key()
                emb = OpenAIEmbeddings()
                vs = FAISS.load_local(str(store_path), emb, allow_dangerous_deserialization=True)
                return vs
            else:
                logger.error("Kopyalama bitti ancak index.faiss bulunamadı.")
        except Exception as copy_err:
            logger.error(f"Repo'dan kopyalama başarısız: {copy_err}")

    # 3) Hugging Face Hub’dan indirmeyi dene
    logger.info("Hugging Face Hub'dan FAISS indirmeyi deniyorum...")
    if try_download_faiss_from_hub(store_path):
        try:
            logger.info("Hub'dan indirilen dosyalar bulundu, FAISS yükleniyor...")
            ensure_openai_key()
            emb = OpenAIEmbeddings()
            vs = FAISS.load_local(str(store_path), emb, allow_dangerous_deserialization=True)
            logger.info("FAISS index (Hub) başarıyla yüklendi.")
            return vs
        except Exception as e:
            logger.error(f"Hub'dan indirildi fakat FAISS yüklenemedi: {e}")

    # 4) İzin varsa runtime'da index üret
    if os.getenv("ALLOW_SCRAPE", "0") == "1":
        logger.info("ALLOW_SCRAPE=1 → Index runtime'da üretilecek. Bu işlem birkaç dakika sürebilir...")
        try:
            if store_path.exists():
                shutil.rmtree(store_path, ignore_errors=True)

            build_index(force_scrape=False, save_chunk_files=False)

            ensure_openai_key()
            emb = OpenAIEmbeddings()
            vs = FAISS.load_local(str(store_path), emb, allow_dangerous_deserialization=True)
            logger.info("FAISS index başarıyla üretildi ve yüklendi.")
            return vs
        except Exception as build_err:
            logger.error(f"Index üretimi başarısız: {build_err}")
            raise RuntimeError(f"Index build failed: {build_err}")

    # 5) Hepsi başarısızsa hata
    error_msg = (
        "FAISS index bulunamadı ve oluşturma izni kapalı.\n"
        f"  - Target path: {store_path}\n"
        f"  - Repo path: data/embeddings/faiss_store\n"
        f"  - HUB_REPO_ID: {os.getenv('HUB_REPO_ID')}\n"
        f"  - ALLOW_SCRAPE: {os.getenv('ALLOW_SCRAPE', '0')}\n"
        "Çözümler:\n"
        "  A) HUB_REPO_ID=ymerta/netmerianbot-faiss (ve gerekirse HF_TOKEN) ekleyin; dosyalar Hub'dan indirilsin.\n"
        "  B) data/embeddings/faiss_store/ içine index.faiss & index.pkl ekleyin.\n"
        "  C) ALLOW_SCRAPE=1 yapıp runtime'da üretin (yavaş olabilir)."
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)

# Application startup
logger.info("Starting NetmerianBot API...")
try:
    vs = load_or_build_faiss()
    docs = list(vs.docstore._dict.values())
    corpus_texts = [d.page_content for d in docs]
    corpus_meta = [d.metadata for d in docs]

    logger.info(f"{len(corpus_texts)} doküman yüklendi.")

    graph = build_app_graph(corpus_texts, corpus_meta, faq_path="data/faq_answers.json")
    APP_READY = True
    APP_ERROR = None
    logger.info("Application ready!")

except Exception as e:
    logger.error(f"Application startup failed: {e}")
    graph = None
    APP_READY = False
    APP_ERROR = str(e)

@app.get("/")
def health():
    return {
        "ok": APP_READY,
        "service": "NetmerianBot API",
        "error": APP_ERROR,
    }

@app.get("/debug")
def debug_info():
    """Debug information"""
    store_path = Path(FAISS_STORE_PATH)
    repo_path = Path("data/embeddings/faiss_store")

    return {
        "app_ready": APP_READY,
        "app_error": APP_ERROR,
        "faiss_store_path": str(store_path),
        "faiss_exists": store_path.exists(),
        "faiss_index_exists": (store_path / "index.faiss").exists() if store_path.exists() else False,
        "repo_faiss_exists": repo_path.exists(),
        "repo_index_exists": (repo_path / "index.faiss").exists() if repo_path.exists() else False,
        "hub_repo_id": os.getenv("HUB_REPO_ID"),
        "hub_subfolder": os.getenv("HUB_SUBFOLDER", "faiss_store"),
        "allow_scrape": os.getenv("ALLOW_SCRAPE", "0"),
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "environment": os.getenv("ENVIRONMENT", "development"),
        "cwd": os.getcwd(),
        # HF cache env’leri (izin/konum kontrolü için faydalı)
        "HF_HOME": os.getenv("HF_HOME"),
        "HF_HUB_CACHE": os.getenv("HF_HUB_CACHE"),
        "HOME": os.getenv("HOME"),
    }

@app.post("/chat", response_model=ChatOut)
def chat(body: ChatIn):
    if not APP_READY or graph is None:
        raise HTTPException(status_code=503, detail=f"Service not ready: {APP_ERROR}")

    try:
        res = graph.invoke({"query": body.query}, config={"run_name": "ChatQuery"})
        return ChatOut(
            answer=res.get("answer") or "",
            citations=res.get("citations") or [],
            suggestions=res.get("suggestions") or [],
        )
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")
