# 🤖 NetmerianBot - GraphRAG Chatbot

Netmera dokümanları için gelişmiş GraphRAG (Graph Retrieval-Augmented Generation) chatbot sistemi.

## 🚀 Özellikler

- **🔗 GraphRAG**: Knowledge Graph + Vector Search hibrit yaklaşımı
- **📱 Streamlit UI**: Modern ve kullanıcı dostu arayüz
- **🔥 Firebase Integration**: Conversation logging ve feedback sistemi
- **⭐ Feedback System**: Gerçek zamanlı kullanıcı değerlendirmeleri
- **🌐 Multi-language**: Türkçe/İngilizce destek

## 🏗️ Sistem Mimarisi

```
User Query → Query Router → Graph/Vector Retrieval → LLM Generation → Response
                ↓
        Feedback Collection → Firebase → Analytics
```

## 📊 GraphRAG İstatistikleri

- **119 Entities**: iOS, Android, Flutter, APIs, Features
- **112 Relationships**: platform dependencies, feature connections
- **3 Retrieval Strategies**: Graph-first, Vector-first, Balanced

## 🚀 Deployment

Bu aplikasyon Streamlit Cloud'da çalışmak üzere optimize edilmiştir.

### Streamlit Cloud Deployment:

1. https://share.streamlit.io adresine git
2. GitHub repository'yi bağla
3. `app.py` dosyasını main file olarak seç
4. Secrets'ları Streamlit Cloud'da ayarla:
   - `OPENAI_API_KEY`
   - `FIREBASE_*` değişkenleri

## 🔧 Local Development

```bash
# Clone repository
git clone <your-repo-url>
cd netmerian-bot-v2

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .streamlit/secrets.toml.template .streamlit/secrets.toml
# secrets.toml dosyasını düzenle

# Run application
streamlit run app.py
```

## 📈 Performance

- **Response Time**: ~2-3 saniye ortalama
- **Accuracy**: GraphRAG ile %30+ improvement
- **Context Quality**: Multi-source retrieval ile zengin context

## 🎯 Use Cases

- iOS/Android integration differences
- Step-by-step setup guides
- Feature comparisons
- Troubleshooting assistance
- API documentation queries

## 🤝 Contribution

1. Fork the repository
2. Create feature branch
3. Add your improvements
4. Submit pull request

## 📞 Support

Issues ve sorular için GitHub Issues kullanın.