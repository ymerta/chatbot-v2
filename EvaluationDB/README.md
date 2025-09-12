# Netmera Chatbot Test Dataset for LangSmith

Bu repository, Netmera platformu hakkında chatbot performansını test etmek için LangSmith ile uyumlu dataset'ler içerir.

## 📁 Dataset Dosyaları

### 1. `netmera_chatbot_dataset.json`
**Format:** LangSmith Key-Value Format
**Içerik:** Temel Netmera özellikleri ve yaygın kullanım senaryoları
**Kayıt Sayısı:** 20 örnek
**Kullanım:** Genel chatbot performans testi

```json
{
  "inputs": {"question": "Netmera nedir?"},
  "outputs": {"answer": "Netmera bir müşteri etkileşim platformudur..."},
  "metadata": {"category": "genel_bilgi", "difficulty": "kolay"}
}
```

### 2. `netmera_chatbot_dataset.csv`
**Format:** CSV (Basit tablo formatı)
**Içerik:** Aynı temel dataset CSV formatında
**Kullanım:** Spreadsheet araçları ile analiz için

### 3. `netmera_extended_dataset.json`
**Format:** LangSmith Key-Value Format (Gelişmiş)
**Içerik:** Teknik detaylar, API specifications, troubleshooting
**Kayıt Sayısı:** 20 örnek
**Kullanım:** Gelişmiş teknik sorular için

### 4. `netmera_chat_dataset.json`
**Format:** LangSmith Chat Format
**Içerik:** Gerçek konuşma senaryoları, multi-turn dialogues
**Kayıt Sayısı:** 5 örnek
**Kullanım:** Conversational AI testi

## 🎯 Test Kategorileri

### Temel Kategoriler
- **genel_bilgi**: Platform tanıtımı ve temel özellikler
- **push_notifications**: Bildirim gönderme ve yönetimi
- **sdk_integration**: Mobil/web SDK entegrasyonu
- **user_segmentation**: Kullanıcı segmentasyonu
- **analytics**: Raporlama ve analitik
- **automation**: Otomatik mesajlaşma

### Gelişmiş Kategoriler
- **troubleshooting**: Sorun çözme
- **api_integration**: API kullanımı
- **ab_testing**: A/B test optimizasyonu
- **personalization**: Kişiselleştirme
- **gdpr_compliance**: Veri gizliliği

## 📊 Zorluk Seviyeleri

- **kolay**: Temel platform bilgileri
- **orta**: Teknik implementasyon
- **zor**: Gelişmiş özellikler ve troubleshooting
- **çok_zor**: Machine learning, predictive analytics

## 🚀 LangSmith'e Yükleme

### Python ile
```python
from langsmith import Client

client = Client()

# Dataset oluştur
dataset = client.create_dataset(
    dataset_name="Netmera Chatbot Test Dataset",
    description="Netmera platformu hakkında chatbot performans testi"
)

# JSON dosyasını yükle
import json
with open('netmera_chatbot_dataset.json', 'r', encoding='utf-8') as f:
    examples = json.load(f)

# Examples'ları ekle
client.create_examples(
    dataset_id=dataset.id,
    examples=examples
)
```

### CSV ile
```python
import pandas as pd

# CSV'yi okу
df = pd.read_csv('netmera_chatbot_dataset.csv')

# LangSmith formatına çevir
examples = []
for _, row in df.iterrows():
    examples.append({
        "inputs": {"question": row['question']},
        "outputs": {"answer": row['answer']},
        "metadata": {
            "category": row['category'],
            "difficulty": row['difficulty'],
            "topic": row['topic']
        }
    })

client.create_examples(dataset_id=dataset.id, examples=examples)
```

## 🔍 Evaluation Metrikleri

### Önerilen Evaluation Kriterleri

1. **Accuracy**: Cevapların teknik doğruluğu
2. **Completeness**: Cevapların kapsamlılığı
3. **Clarity**: Açıklama netliği
4. **Helpfulness**: Kullanıcı için faydalılık
5. **Response Time**: Yanıt hızı

### Custom Evaluators

```python
def netmera_accuracy_evaluator(run, example):
    """Netmera-specific technical accuracy check"""
    # Implementation details...
    pass

def netmera_completeness_evaluator(run, example):
    """Check if response covers all necessary steps"""
    # Implementation details...
    pass
```

## 📋 Test Senaryoları

### Temel Kullanım
- Platform tanıtımı
- Hesap oluşturma
- İlk kampanya kurulumu

### SDK Integration
- Android/iOS SDK kurulumu
- Web SDK implementasyonu
- API key yapılandırması

### Campaign Management
- Push notification oluşturma
- Segmentasyon
- A/B testing
- Scheduling

### Analytics & Optimization
- Rapor okuma
- Performance optimization
- ROI calculation

### Troubleshooting
- Delivery issues
- Certificate problems
- API errors

## 🎨 Kullanım Örnekleri

### Scenario 1: Yeni Kullanıcı Onboarding
Test chatbot'un yeni kullanıcılara Netmera'yı nasıl tanıttığını değerlendirin.

### Scenario 2: Teknik Destek
Geliştiricilerin SDK entegrasyonu sırasında karşılaştığı sorunları çözme becerisi.

### Scenario 3: Marketing Optimization
Pazarlama ekiplerinin kampanya performansını artırma konusunda aldığı tavsiyelerin kalitesi.

## 🔧 Customization

### Yeni Kategoriler Ekleme
```json
{
  "inputs": {"question": "Yeni özellik sorusu"},
  "outputs": {"answer": "Detaylı cevap"},
  "metadata": {
    "category": "yeni_kategori",
    "difficulty": "orta",
    "topic": "özel_konu",
    "use_case": "specific_scenario"
  }
}
```

### Industry-Specific Scenarios
Dataset'i belirli sektörler için customize edebilirsiniz:
- E-commerce
- Gaming
- Finance
- Healthcare

## 📈 Performance Tracking

### Benchmark Metrikleri
- **Response Accuracy**: >90%
- **Query Coverage**: >95%
- **Response Time**: <2 seconds
- **User Satisfaction**: >4.5/5

### Monitoring
- Weekly performance reviews
- Monthly dataset updates
- Quarterly benchmark evaluations

## 🤝 Katkıda Bulunma

1. Yeni senaryolar ekleyin
2. Edge case'leri test edin
3. Performance feedback'i paylaşın
4. Documentation'ı geliştirin

## 📞 Destek

Sorularınız için:
- GitHub Issues
- [Your Contact Information]

## 📄 Lisans

Bu dataset MIT lisansı altında sunulmaktadır.

---

**Not:** Bu dataset Netmera User Guide ve Developer Guide'a dayanarak oluşturulmuştur. Gerçek production kullanımından önce content'i review edin ve validate edin.
