import os, json
import streamlit as st
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings

from src.config import FAISS_STORE_PATH
from src.graph.app_graph import build_app_graph

st.set_page_config(page_title="NetmerianBot (LangGraph)", layout="centered")

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
graph = build_app_graph(corpus_texts, corpus_meta)

# --- yardımcı: URL'i okunur başlığa çevir
def prettify(u: str) -> str:
    u2 = u.replace("https://user.netmera.com/netmera-user-guide/", "")
    u2 = u2.replace("https://user.netmera.com/netmera-developer-guide/", "")
    return u2.replace("-", " ").replace("/", " > ").title()

# 3) UI
st.title("🤖 NetmerianBot — LangGraph")

if "history" not in st.session_state:
    st.session_state.history = []

user_q = st.chat_input("Bir soru yazın…")

if user_q:
    with st.spinner("Yanıt hazırlanıyor..."):
        result = graph.invoke({"query": user_q})
    answer = result.get("answer") or ""
    cites  = result.get("citations") or []
    suggs  = result.get("suggestions") or []

    st.session_state.history.append(("user", user_q))
    st.session_state.history.append(("assistant", answer, cites, suggs))

for item in st.session_state.history:
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