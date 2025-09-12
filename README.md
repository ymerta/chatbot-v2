---
title: Netmerian Bot V2
emoji: 🔥
colorFrom: gray
colorTo: purple
sdk: docker
pinned: false
---

# 🤖 Netmerian Bot V2

Netmera için geliştirilmiş akıllı chatbot sistemi. LangGraph kullanarak multi-step reasoning ve LangSmith ile comprehensive evaluation sistemi.

## 🚀 Özellikler

- **Hybrid Retrieval**: FAISS + BM25 + Fuzzy Search kombinasyonu
- **Multi-language Support**: Türkçe ve İngilizce desteği
- **LangGraph Integration**: Akıllı conversation flow yönetimi
- **LangSmith Evaluation**: Comprehensive performance tracking
- **Real-time Analytics**: Detaylı performance raporları

## 📋 Kurulum

### 1. Dependencies
```bash
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
cp evaluation.env.example evaluation.env
# API key'lerinizi evaluation.env dosyasına ekleyin
```

### 3. Data Preparation
```bash
python src/index_build.py  # Embeddings oluştur
```

## 🎯 Kullanım

### Chatbot'u Çalıştır
```bash
streamlit run app.py
```

### Evaluation Sistemi

#### Quick Setup
```bash
python setup_evaluation.py
```

#### Evaluation Çalıştır
```bash
# Tek dataset
python evaluate_chatbot.py --dataset netmera-basic-qa

# Tüm dataset'ler
python evaluate_chatbot.py --dataset all

# Custom experiment
python evaluate_chatbot.py --dataset netmera-advanced-qa --experiment my_test
```

#### Reports Oluştur
```bash
# Son 7 günün evaluations
python -m src.evaluation.reporting --recent 7

# Belirli experiments
python -m src.evaluation.reporting --experiments exp1 exp2 exp3
```

## 📊 Evaluation Datasets

Sistem üç farklı dataset kullanır:

1. **netmera-basic-qa**: Temel Netmera özellikleri (~20 examples)
2. **netmera-advanced-qa**: Teknik detaylar ve troubleshooting (~20 examples)  
3. **netmera-chat-scenarios**: Multi-turn konuşmalar (~5 scenarios)

## 🔍 Evaluation Metrics

- **Accuracy (30%)**: Teknik doğruluk ve Netmera terminolojisi
- **Completeness (25%)**: Cevapların kapsamlılığı
- **Helpfulness (25%)**: Kullanıcı için pratik değer
- **Language Consistency (20%)**: Dil tutarlılığı

## 📈 Performance Benchmarks

| Metric | Excellent | Good | Acceptable |
|--------|-----------|------|------------|
| Accuracy | ≥0.90 | ≥0.75 | ≥0.60 |
| Completeness | ≥0.85 | ≥0.70 | ≥0.55 |
| Helpfulness | ≥0.80 | ≥0.65 | ≥0.50 |

## 🛠️ Geliştirme

### Demo Çalıştır
```bash
python run_evaluation_demo.py
```

### Custom Evaluator Ekle
```python
from langsmith.schemas import Run, Example

def custom_evaluator(run: Run, example: Example) -> dict:
    # Custom evaluation logic
    return {"key": "custom_metric", "score": score, "reason": reason}
```

## 📚 Dokümantasyon

- **Evaluation System**: [EVALUATION_README.md](EVALUATION_README.md)
- **API Reference**: Kod içi dokümantasyon
- **LangSmith Dashboard**: https://smith.langchain.com/

## 🤝 Katkıda Bulunma

1. Yeni evaluation scenarios ekleyin
2. Custom evaluators geliştirin  
3. Performance optimizasyonları yapın
4. Documentation'ı geliştirin

## 🔗 Links

- **LangSmith**: https://smith.langchain.com/
- **Netmera Docs**: https://user.netmera.com/
- **HuggingFace Space**: https://huggingface.co/docs/hub/spaces-config-reference
