# 🤖 Netmera Chatbot LangSmith Evaluation System

Bu doküman, Netmera chatbot'unun performansını LangSmith kullanarak nasıl değerlendireceğinizi açıklar.

## 📋 İçindekiler

- [Kurulum](#kurulum)
- [Hızlı Başlangıç](#hızlı-başlangıç)
- [Dataset'ler](#datasetler)
- [Evaluation Metrikleri](#evaluation-metrikleri)
- [Kullanım Örnekleri](#kullanım-örnekleri)
- [Reporting](#reporting)
- [Troubleshooting](#troubleshooting)

## 🚀 Kurulum

### 1. Gerekli Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Variables

`evaluation.env.example` dosyasını `evaluation.env` olarak kopyalayın ve gerçek değerleri girin:

```bash
cp evaluation.env.example evaluation.env
```

Gerekli environment variables:

```bash
# LangSmith Configuration (Zorunlu)
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=netmera-chatbot-evaluation

# OpenAI Configuration (Zorunlu)
OPENAI_API_KEY=your_openai_api_key_here

# Optional Settings
CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large
```

### 3. LangSmith API Key Alın

1. [LangSmith](https://smith.langchain.com/) hesabı oluşturun
2. API key'inizi alın: Settings → API Keys → Create API Key
3. Environment variable'a ekleyin

## ⚡ Hızlı Başlangıç

### Tek Komutla Evaluation

```bash
# Tüm dataset'leri evaluate et
python evaluate_chatbot.py --dataset all

# Belirli bir dataset'i evaluate et
python evaluate_chatbot.py --dataset netmera-basic-qa

# Özel experiment adıyla
python evaluate_chatbot.py --dataset netmera-advanced-qa --experiment my_test_run
```

### Python Kodu ile

```python
from src.evaluation import NetmeraEvaluator, run_evaluation
import asyncio

# Evaluator'ı initialize et
evaluator = NetmeraEvaluator()

# Dataset'leri oluştur
evaluator.create_dataset(
    "my-test-dataset",
    "netmera_chatbot_dataset.json", 
    "Test dataset"
)

# Evaluation'ı çalıştır
results = asyncio.run(run_evaluation(
    evaluator, 
    "my-test-dataset", 
    "my_experiment"
))
```

## 📊 Dataset'ler

Sistem, `EvaluationDB/` klasöründeki mevcut dataset'leri kullanır:

### 1. netmera-basic-qa
- **Dosya**: `netmera_chatbot_dataset.json`
- **İçerik**: Temel Netmera özellikleri ve kullanım senaryoları
- **Örnekler**: ~20 soru-cevap çifti
- **Kategoriler**: genel_bilgi, push_notifications, sdk_integration, user_segmentation

### 2. netmera-advanced-qa  
- **Dosya**: `netmera_extended_dataset.json`
- **İçerik**: Gelişmiş teknik konular ve troubleshooting
- **Örnekler**: ~20 teknik soru-cevap çifti
- **Kategoriler**: troubleshooting, api_integration, ab_testing, personalization

### 3. netmera-chat-scenarios
- **Dosya**: `netmera_chat_dataset.json`  
- **İçerik**: Multi-turn konuşma senaryoları
- **Örnekler**: ~5 gerçek chat senaryosu
- **Kategoriler**: support, technical_support, guidance, educational

## 🎯 Evaluation Metrikleri

### 1. Accuracy (Doğruluk) - %30 ağırlık
- Teknik doğruluk ve Netmera terminolojisi
- Netmera terimlerinin doğru kullanımı
- Kod örneklerinin doğruluğu
- **Hedef**: ≥0.7

### 2. Completeness (Kapsamlılık) - %25 ağırlık  
- Cevapların kapsamlılığı ve detay seviyesi
- Adım adım açıklamalar
- Örnekler ve alternatifler
- **Hedef**: ≥0.6

### 3. Helpfulness (Faydalılık) - %25 ağırlık
- Kullanıcı için pratik değer
- Actionable tavsiyeler  
- Problem çözme odaklılık
- **Hedef**: ≥0.6

### 4. Language Consistency (Dil Tutarlılığı) - %20 ağırlık
- Türkçe/İngilizce tutarlılığı
- Karışık dil kullanımı tespiti
- **Hedef**: ≥0.8

## 💻 Kullanım Örnekleri

### Örnek 1: Temel Evaluation

```bash
# Config'i kontrol et
python -c "from src.evaluation.config import print_config_status; print_config_status()"

# Dataset'leri listele
python evaluate_chatbot.py --list-datasets

# Temel evaluation
python evaluate_chatbot.py --dataset netmera-basic-qa
```

### Örnek 2: Comprehensive Analysis

```bash
# Tüm dataset'lerde evaluation
python evaluate_chatbot.py --dataset all --experiment comprehensive_test

# Report oluştur
python -m src.evaluation.reporting --recent 1
```

### Örnek 3: Custom Evaluation

```python
from src.evaluation import NetmeraEvaluator
from src.evaluation.reporting import EvaluationReporter

# Custom evaluator
evaluator = NetmeraEvaluator()

# Yeni dataset oluştur  
dataset_id = evaluator.create_dataset(
    "custom-netmera-qa",
    "my_custom_dataset.json",
    "Custom evaluation dataset"
)

# Evaluation çalıştır
import asyncio
results = asyncio.run(run_evaluation(
    evaluator,
    "custom-netmera-qa", 
    "custom_experiment"
))

# Report oluştur
reporter = EvaluationReporter()
reports = reporter.generate_comprehensive_report(["custom_experiment"])
```

## 📈 Reporting

### Otomatik Report Generation

```bash
# Son 7 günün experiment'leri için report
python -m src.evaluation.reporting --recent 7

# Belirli experiment'ler için
python -m src.evaluation.reporting --experiments exp1 exp2 exp3

# Custom output
python -m src.evaluation.reporting --experiments my_exp --output custom_report
```

### Report Formatları

1. **HTML Report** (interactive)
   - Performance charts
   - Detailed metrics table  
   - Recommendations
   - Benchmark comparisons

2. **CSV Export** (data analysis)
   - Raw scores per example
   - Timestamp tracking
   - Easy pivot/analysis

3. **JSON Export** (programmatic)
   - Machine-readable format
   - API integration
   - Custom processing

### Report Lokasyonu

Reports şu klasörde oluşturulur:
```
./evaluation_reports/
├── evaluation_report_20231211_143022.html
├── evaluation_report_20231211_143022.csv  
├── evaluation_report_20231211_143022.json
├── evaluation_scores_20231211_143022.png
└── dataset_comparison_20231211_143022.png
```

## 🔧 Advanced Usage

### Custom Evaluators

```python
from langsmith.schemas import Run, Example

def custom_netmera_evaluator(run: Run, example: Example) -> dict:
    """Custom evaluation logic"""
    prediction = run.outputs.get("answer", "")
    
    # Custom scoring logic
    score = 0.0
    if "netmera" in prediction.lower():
        score += 0.5
    if any(term in prediction for term in ["push", "campaign", "segment"]):
        score += 0.3
    
    return {
        "key": "custom_metric",
        "score": score,
        "reason": "Custom evaluation criteria"
    }

# Add to evaluation
from langsmith.evaluation import evaluate

evaluate(
    predictor_func,
    data="dataset_name",
    evaluators=[custom_netmera_evaluator],
    experiment_prefix="custom_eval"
)
```

### Batch Processing

```python
import asyncio
from src.evaluation import NetmeraEvaluator, run_evaluation

async def batch_evaluation():
    evaluator = NetmeraEvaluator()
    
    datasets = ["netmera-basic-qa", "netmera-advanced-qa", "netmera-chat-scenarios"]
    
    tasks = []
    for dataset in datasets:
        task = run_evaluation(evaluator, dataset, f"batch_{dataset}")
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

# Run batch evaluation
results = asyncio.run(batch_evaluation())
```

### Performance Monitoring

```python
from src.evaluation.reporting import EvaluationReporter

reporter = EvaluationReporter()

# Son 30 günün trendleri
experiments = reporter.get_recent_experiments(30)
summaries = [reporter.analyze_experiment(exp) for exp in experiments]

# Performance trend analysis
for summary in summaries:
    print(f"{summary.experiment_name}: Accuracy={summary.average_scores.get('accuracy', 0):.3f}")
```

## 🔍 Benchmark'lar ve Hedefler

### Performance Tier'ları

| Metric | Excellent | Good | Acceptable | Poor |
|--------|-----------|------|------------|------|
| Accuracy | ≥0.90 | ≥0.75 | ≥0.60 | <0.60 |
| Completeness | ≥0.85 | ≥0.70 | ≥0.55 | <0.55 |
| Helpfulness | ≥0.80 | ≥0.65 | ≥0.50 | <0.50 |
| Language Consistency | ≥0.95 | ≥0.85 | ≥0.70 | <0.70 |

### Response Time Benchmarks

| Category | Target | Good | Acceptable |
|----------|--------|------|------------|
| Simple Q&A | <2s | <5s | <10s |
| Complex Technical | <5s | <8s | <15s |  
| Multi-turn Chat | <3s | <6s | <12s |

## 🔧 Troubleshooting

### Common Issues

#### 1. LANGSMITH_API_KEY bulunamıyor
```bash
export LANGSMITH_API_KEY="your_key_here"
# veya evaluation.env dosyasında set edin
```

#### 2. Dataset dosyası bulunamıyor
```bash
# EvaluationDB klasörünü kontrol edin
ls -la EvaluationDB/
```

#### 3. FAISS store yükleme hatası
```bash
# Data klasörünü kontrol edin
ls -la data/embeddings/faiss_store/
```

#### 4. OpenAI API rate limiting
```
# Model'i değiştirin (config.py)
CHAT_MODEL = "gpt-3.5-turbo"  # instead of gpt-4o
```

### Debug Mode

```python
import logging

# Debug logging aktif et
logging.basicConfig(level=logging.DEBUG)

# Evaluator'da verbose mode
evaluator = NetmeraEvaluator()
evaluator.debug = True
```

### Configuration Check

```bash
python -c "
from src.evaluation.config import validate_config, print_config_status
errors = validate_config()
if errors:
    print('❌ Configuration errors:')
    for error in errors: print(f'  - {error}')
else:
    print('✅ Configuration is valid')
print_config_status()
"
```

## 📚 API Reference

### NetmeraEvaluator

```python
class NetmeraEvaluator:
    def __init__(self, api_key=None, project_name="netmera-chatbot-evaluation")
    def create_dataset(self, dataset_name: str, dataset_file: str, description: str) -> str
    def list_datasets(self) -> List[Dict]
    def chatbot_predictor(self, inputs: Dict[str, Any]) -> Dict[str, Any]
```

### EvaluationReporter

```python
class EvaluationReporter:
    def __init__(self, langsmith_client=None)
    def analyze_experiment(self, experiment_name: str) -> EvaluationSummary
    def generate_html_report(self, summaries: List[EvaluationSummary]) -> Path
    def generate_comprehensive_report(self, experiment_names: List[str]) -> Dict[str, Path]
```

## 🤝 Katkıda Bulunma

### Yeni Evaluator Ekleme

1. `src/evaluation/langsmith_evaluator.py`'da yeni evaluator function tanımlayın
2. `EVALUATOR_CONFIGS`'e configuration ekleyin  
3. Test edin ve dokümante edin

### Yeni Dataset Ekleme

1. `EvaluationDB/` klasörüne JSON dosyası ekleyin
2. `src/evaluation/config.py`'da `DATASET_CONFIGS`'e ekleyin
3. Schema'nın doğru olduğunu kontrol edin

### Performance İyileştirmeleri  

1. Async/await pattern'lerini kullanın
2. Batch processing'i optimize edin
3. Caching stratejileri implementasyonları

## 📞 Destek

- **GitHub Issues**: Sorunlar ve özellik istekleri için
- **Documentation**: Bu README ve kod dokümantasyonu
- **LangSmith Docs**: https://docs.smith.langchain.com/

## 📄 Lisans

Bu evaluation sistemi MIT lisansı altında sunulmuştur.
