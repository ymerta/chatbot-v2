import os, json
import streamlit as st
import uuid
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, firestore
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from src.config import FAISS_STORE_PATH
from src.graph.app_graph import build_app_graph

st.set_page_config(page_title="NetmerianBot (LangGraph)", layout="centered")

# Firebase setup
def init_firebase():
    """Initialize Firebase connection"""
    try:
        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            # Use service account from secrets
            cred_dict = {
                "type": "service_account",
                "project_id": st.secrets["FIREBASE_PROJECT_ID"],
                "private_key_id": st.secrets["FIREBASE_PRIVATE_KEY_ID"],
                "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
                "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
                "client_id": st.secrets["FIREBASE_CLIENT_ID"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{st.secrets['FIREBASE_CLIENT_EMAIL']}"
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        # Get Firestore client
        db = firestore.client()
        print("✅ Firebase connection successful")
        return db
        
    except Exception as e:
        print(f"⚠️ Firebase connection failed: {e}")
        return None

# Initialize Firebase
firebase_db = init_firebase()

# 1) FAISS store’dan (LangChain) dokümanları hafızaya al
emb = OpenAIEmbeddings()
vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
docs = vs.docstore._dict  # id -> Document

corpus_texts = []
corpus_meta  = []
for _id, d in docs.items():
    corpus_texts.append(d.page_content)
    corpus_meta.append(d.metadata)  # {"source":..., "url":...}

# 2) Graph compile
# GraphRAG toggle option
use_graphrag = st.sidebar.checkbox("🔗 GraphRAG Kullan", value=True, help="Knowledge Graph tabanlı hibrit arama")
graph = build_app_graph(corpus_texts, corpus_meta, use_graphrag=use_graphrag)

# --- yardımcı: URL'i okunur başlığa çevir
def prettify(u: str) -> str:
    u2 = u.replace("https://user.netmera.com/netmera-user-guide/", "")
    u2 = u2.replace("https://user.netmera.com/netmera-developer-guide/", "")
    return u2.replace("-", " ").replace("/", " > ").title()

def log_conversation_to_firebase(conversation_id, user_message, assistant_response, context_docs=None, lang="English"):
    """Log conversation to Firebase with integrated feedback structure"""
    try:
        if firebase_db is None:
            print("⚠️ Firebase not available, skipping conversation log")
            return None
            
        doc_id = str(uuid.uuid4())
        conversation_log = {
            # Conversation Data
            "conversation_id": conversation_id,
            "user_message": user_message,
            "assistant_response": assistant_response,
            "language": lang,
            "context_docs": context_docs or [],
            "timestamp": datetime.now(),
            
            # Feedback Data (initially empty)
            "rating": None,
            "score": None,
            "feedback_text": "",
            "comment": "",
            "feedback_timestamp": None,
            "has_feedback": False,
            
            # Type
            "type": "conversation_with_feedback"
        }
        
        # Insert to Firebase
        firebase_db.collection('conversations').document(doc_id).set(conversation_log)
        
        # Store the document ID for feedback linking
        st.session_state.last_conversation_id = doc_id
        
        print(f"✅ Conversation logged to Firebase: {doc_id}")
        return doc_id
        
    except Exception as e:
        print(f"❌ Firebase logging error: {e}")
        return None

def submit_feedback_to_firebase(rating, feedback_text="", conversation_id="", user_message="", conversation_doc_id=None):
    """Update existing conversation document with feedback"""
    try:
        if firebase_db is None:
            st.error("❌ Firebase bağlantısı yok")
            return False
        
        # Get the most recent conversation_doc_id if not provided
        if not conversation_doc_id:
            conversation_doc_id = st.session_state.get("last_conversation_id")
        
        if not conversation_doc_id:
            st.error("❌ Conversation ID bulunamadı")
            return False
        
        # Prepare feedback data
        feedback_comment = ""
        if feedback_text and feedback_text.strip():
            feedback_comment = f"⭐ Rating: {rating}/5 stars\n💬 Comment: {feedback_text.strip()}"
        else:
            feedback_comment = f"⭐ User rated {rating}/5 stars"
        
        # Update the existing conversation document with feedback
        feedback_data = {
            "rating": rating,
            "score": rating / 5.0,  # Normalized score (0-1)
            "feedback_text": feedback_text.strip() if feedback_text else "",
            "comment": feedback_comment,
            "feedback_timestamp": datetime.now(),
            "has_feedback": True
        }
        
        # Update Firebase document
        firebase_db.collection('conversations').document(conversation_doc_id).update(feedback_data)
        
        st.success(f"✅ Rating Firebase'e kaydedildi: {rating}/5 ⭐")
        print(f"✅ Feedback updated in Firebase: {conversation_doc_id}")
        return True
        
    except Exception as e:
        st.error(f"❌ Firebase feedback error: {str(e)}")
        print(f"Firebase feedback error details: {e}")
        return False

def render_feedback_ui(message_index, lang="Turkish"):
    """Render feedback UI for a specific message"""
    message_id = f"msg_{message_index}"
    
    if message_id not in st.session_state.message_ratings:
        # Step 1: Rating selection
        feedback_text = "Bu yanıt ne kadar faydalıydı?" if lang == "Türkçe" else "How helpful was this response?"
        st.write(f"**{feedback_text}**")
        
        rating_cols = st.columns(5)
        for i in range(1, 6):
            with rating_cols[i-1]:
                if st.button("⭐" if i <= 3 else "🌟", key=f"rate_{message_id}_{i}", help=f"{i}/5"):
                    st.session_state.message_ratings[message_id] = {
                        "rating": i,
                        "timestamp": datetime.now().isoformat(),
                        "conversation_doc_id": st.session_state.get("last_conversation_id"),
                        "awaiting_comment": True  # Flag to show comment input
                    }
                    st.rerun()
                    
    elif st.session_state.message_ratings[message_id].get("awaiting_comment", False):
        # Step 2: Optional comment input
        rating = st.session_state.message_ratings[message_id]["rating"]
        stars = "⭐" * rating + "☆" * (5 - rating)
        
        st.success(f"Rating: {stars}")
        
        comment_label = "Opsiyonel yorum ekleyin:" if lang == "Türkçe" else "Add optional comment:"
        placeholder = "Yanıt hakkında düşüncelerinizi paylaşın..." if lang == "Türkçe" else "Share your thoughts about the response..."
        
        user_comment = st.text_area(
            comment_label,
            placeholder=placeholder,
            key=f"comment_{message_id}",
            height=80
        )
        
        col1, col2 = st.columns(2)
        with col1:
            skip_text = "Yorum yazmadan devam et" if lang == "Türkçe" else "Skip comment"
            if st.button(skip_text, key=f"skip_{message_id}"):
                # Submit without comment
                submit_feedback_to_firebase(
                    rating, 
                    "", 
                    st.session_state.conversation_id,
                    f"Message {message_index}",
                    st.session_state.get("last_conversation_id")
                )
                st.session_state.message_ratings[message_id]["awaiting_comment"] = False
                st.session_state.message_ratings[message_id]["comment"] = ""
                st.rerun()
        
        with col2:
            submit_text = "Yorumla birlikte gönder" if lang == "Türkçe" else "Submit with comment"
            if st.button(submit_text, key=f"submit_{message_id}"):
                # Submit with comment
                submit_feedback_to_firebase(
                    rating, 
                    user_comment, 
                    st.session_state.conversation_id,
                    f"Message {message_index}",
                    st.session_state.get("last_conversation_id")
                )
                st.session_state.message_ratings[message_id]["awaiting_comment"] = False
                st.session_state.message_ratings[message_id]["comment"] = user_comment
                st.rerun()
                
    else:
        # Step 3: Show completed feedback
        rating_data = st.session_state.message_ratings[message_id]
        rating = rating_data["rating"]
        comment = rating_data.get("comment", "")
        
        stars = "⭐" * rating + "☆" * (5 - rating)
        
        if comment:
            thanks_msg = f"Değerlendirmeniz: {stars}" if lang == "Türkçe" else f"Your rating: {stars}"
            st.success(thanks_msg)
            comment_label = "Yorumunuz:" if lang == "Türkçe" else "Your comment:"
            st.info(f"**{comment_label}** {comment}")
        else:
            thanks_msg = f"Değerlendirmeniz: {stars} - Teşekkürler!" if lang == "Türkçe" else f"Your rating: {stars} - Thank you!"
            st.info(thanks_msg)

# 3) UI
st.title("🤖 NetmerianBot — LangGraph")

# Firebase status indicator
if firebase_db is None:
    st.error("⚠️ Firebase bağlantısı yok - Feedback sistemi çalışmayacak")
    with st.expander("Firebase kurulum bilgisi"):
        st.code("""
Firebase credentials eksik veya hatalı.
Streamlit secrets'da Firebase service account bilgilerini kontrol edin:
- FIREBASE_PROJECT_ID
- FIREBASE_PRIVATE_KEY
- FIREBASE_CLIENT_EMAIL
- vb.
        """)
else:
    st.success("✅ Firebase bağlantısı aktif - Feedback sistemi hazır")

# GraphRAG status indicator
if use_graphrag:
    try:
        from src.graphrag.graph_store import NetmeraGraphStore
        graph_store = NetmeraGraphStore()
        stats = graph_store.get_stats()
        st.info(f"🔗 GraphRAG aktif: {stats['total_nodes']} node, {stats['total_edges']} edge")
    except Exception as e:
        st.warning(f"🟡 GraphRAG başlatılamadı: {str(e)[:100]}...")
else:
    st.info("📊 Geleneksel FAISS+BM25 modu aktif")

if "history" not in st.session_state:
    st.session_state.history = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = str(uuid.uuid4())
if "message_ratings" not in st.session_state:
    st.session_state.message_ratings = {}
if "last_conversation_id" not in st.session_state:
    st.session_state.last_conversation_id = None

user_q = st.chat_input("Bir soru yazın…")

if user_q:
    with st.spinner("Yanıt hazırlanıyor..."):
        result = graph.invoke({"query": user_q})
    answer = result.get("answer") or ""
    cites  = result.get("citations") or []
    suggs  = result.get("suggestions") or []

    st.session_state.history.append(("user", user_q))
    st.session_state.history.append(("assistant", answer, cites, suggs))
    
    # Log conversation to Firebase
    log_conversation_to_firebase(
        conversation_id=st.session_state.conversation_id,
        user_message=user_q,
        assistant_response=answer,
        context_docs=[{"citations": cites, "suggestions": suggs}],
        lang="Turkish"
    )

for i, item in enumerate(st.session_state.history):
    role = item[0]
    if role == "user":
        st.chat_message("user").markdown(item[1])
    else:
        _, answer, cites, suggs = item
        with st.chat_message("assistant"):
            st.markdown(answer)

            # --- DEĞİŞEN KISIM: tek, prettify edilmiş kaynak linki
            if cites:
                primary = cites[0]
                st.markdown(f"📄 **Kaynak belge**: [{prettify(primary)}]({primary})")

                # (İsteğe bağlı) başka citation varsa küçük bir detay olarak göster
                if len(cites) > 1:
                    with st.expander("Diğer ilgili kaynaklar"):
                        for extra in cites[1:]:
                            st.markdown(f"- [{prettify(extra)}]({extra})")

            if suggs:
                st.info("Öneriler:\n- " + "\n- ".join(suggs))
            
            # Add feedback UI for assistant messages
            st.markdown("---")
            with st.container():
                render_feedback_ui(i, "Türkçe")