#!/usr/bin/env python3
"""
Netmera Chatbot Evaluation Demo Script
Bu script, evaluation sisteminin nasıl kullanılacağını gösterir.
"""

import os
import sys
import asyncio
from pathlib import Path

def demo_basic_usage():
    """Temel kullanım demo'su"""
    print("📚 DEMO 1: Temel Evaluation Kullanımı")
    print("=" * 50)
    
    print("""
# 1. Environment setup kontrolü
python setup_evaluation.py

# 2. Mevcut dataset'leri listele  
python evaluate_chatbot.py --list-datasets

# 3. Türkçe Developer Guide dataset evaluation
python evaluate_chatbot.py --dataset netmera-developer-guide

# 4. Türkçe User guide dataset evaluation
python evaluate_chatbot.py --dataset netmera-user-guide

# 5. İngilizce Developer Guide dataset evaluation
python evaluate_chatbot.py --dataset netmera-developer-guide-en

# 6. İngilizce User Guide dataset evaluation
python evaluate_chatbot.py --dataset netmera-user-guide-en

# 7. Tüm dataset'leri evaluate et (Türkçe + İngilizce)
python evaluate_chatbot.py --dataset all

# 8. Custom experiment adıyla
python evaluate_chatbot.py --dataset netmera-developer-guide --experiment my_test
""")


def demo_python_api():
    """Python API kullanım demo'su"""
    print("\n📚 DEMO 2: Python API Kullanımı")
    print("=" * 50)
    
    print("""
from src.evaluation import NetmeraEvaluator, run_evaluation
import asyncio

# Evaluator oluştur
evaluator = NetmeraEvaluator(project_name="my-evaluation-project")

# Mevcut dataset'leri listele
datasets = evaluator.list_datasets()
print(f"Mevcut dataset sayısı: {len(datasets)}")

# Yeni dataset oluştur
dataset_id = evaluator.create_dataset(
    "my-custom-dataset",
    "netmera_developer_guide_dataset.json", 
    "Özel test dataset'i"
)

# Evaluation çalıştır
async def run_my_evaluation():
    results = await run_evaluation(
        evaluator,
        "my-custom-dataset",
        "custom_experiment_20231211"
    )
    return results

# Async evaluation çalıştır
results = asyncio.run(run_my_evaluation())
""")


def demo_reporting():
    """Reporting demo'su"""
    print("\n📚 DEMO 3: Reporting ve Analiz")
    print("=" * 50)
    
    print("""
from src.evaluation.reporting import EvaluationReporter

# Reporter oluştur
reporter = EvaluationReporter()

# Son 7 günün experiment'lerini getir
recent_experiments = reporter.get_recent_experiments(7)
print(f"Son 7 günde {len(recent_experiments)} experiment yapıldı")

# Belirli bir experiment'ı analiz et
summary = reporter.analyze_experiment("my_experiment_20231211")
print(f"Accuracy: {summary.average_scores.get('accuracy', 0):.3f}")
print(f"Completeness: {summary.average_scores.get('completeness', 0):.3f}")

# Comprehensive report oluştur
reports = reporter.generate_comprehensive_report([
    "experiment_1", 
    "experiment_2", 
    "experiment_3"
])

# Report dosyaları:
# - HTML: Interactive dashboard
# - CSV: Data analysis için  
# - JSON: Programmatic access için
""")


def demo_custom_evaluators():
    """Custom evaluator demo'su"""
    print("\n📚 DEMO 4: Custom Evaluators")
    print("=" * 50)
    
    print("""
from langsmith.schemas import Run, Example
from langsmith.evaluation import evaluate

def netmera_specific_evaluator(run: Run, example: Example) -> dict:
    \"\"\"Netmera'ya özel custom evaluator\"\"\"
    prediction = run.outputs.get("answer", "").lower()
    
    score = 0.0
    feedback = []
    
    # Netmera terimleri kontrolü
    netmera_terms = ["push notification", "segment", "campaign", "sdk"]
    used_terms = [term for term in netmera_terms if term in prediction]
    
    if used_terms:
        score += 0.4
        feedback.append(f"Netmera terimleri kullanıldı: {used_terms}")
    
    # Kod örneği kontrolü  
    if any(code_word in prediction for code_word in ["gradle", "json", "api", "method"]):
        score += 0.3
        feedback.append("Kod örnekleri var")
    
    # Problem çözme odaklılık
    if any(solution in prediction for solution in ["çözüm", "solution", "fix", "adım"]):
        score += 0.3
        feedback.append("Problem çözme odaklı")
    
    return {
        "key": "netmera_specific",
        "score": min(score, 1.0),
        "reason": "; ".join(feedback) if feedback else "Basic response"
    }

# Custom evaluator'ı kullan
results = evaluate(
    lambda inputs: evaluator.chatbot_predictor(inputs),
    data="netmera-developer-guide",
    evaluators=[netmera_specific_evaluator],
    experiment_prefix="custom_eval"
)
""")


def demo_advanced_analysis():
    """Gelişmiş analiz demo'su"""
    print("\n📚 DEMO 5: Gelişmiş Analiz ve Monitoring")
    print("=" * 50)
    
    print("""
import pandas as pd
from src.evaluation.reporting import EvaluationReporter

# Reporter oluştur
reporter = EvaluationReporter()

# Son 30 günün verilerini al
experiments = reporter.get_recent_experiments(30)
summaries = [reporter.analyze_experiment(exp) for exp in experiments]

# Performance trend analizi
df_data = []
for summary in summaries:
    df_data.append({
        'date': summary.timestamp,
        'experiment': summary.experiment_name,
        'dataset': summary.dataset_name,
        'accuracy': summary.average_scores.get('accuracy', 0),
        'completeness': summary.average_scores.get('completeness', 0),
        'helpfulness': summary.average_scores.get('helpfulness', 0)
    })

df = pd.DataFrame(df_data)

# Haftalık ortalama performance
weekly_avg = df.groupby(df['date'].dt.week)[['accuracy', 'completeness', 'helpfulness']].mean()
print("Haftalık performance trendi:")
print(weekly_avg)

# Dataset'e göre performance karşılaştırması
dataset_performance = df.groupby('dataset')[['accuracy', 'completeness', 'helpfulness']].mean()
print("\\nDataset performance karşılaştırması:")
print(dataset_performance)

# Benchmark'ların altında kalan alanlar
poor_performance = df[df['accuracy'] < 0.6][['experiment', 'dataset', 'accuracy']]
if not poor_performance.empty:
    print("\\n⚠️ Benchmark'ın altındaki performans:")
    print(poor_performance)
""")


def demo_automation():
    """Automation demo'su"""
    print("\n📚 DEMO 6: Automated Evaluation Pipeline")
    print("=" * 50)
    
    print("""
# evaluation_pipeline.py
import schedule
import time
from datetime import datetime
from src.evaluation import NetmeraEvaluator, run_evaluation
from src.evaluation.reporting import EvaluationReporter

async def daily_evaluation():
    \"\"\"Günlük otomatik evaluation\"\"\"
    evaluator = NetmeraEvaluator()
    
    # Tüm dataset'lerde evaluation çalıştır
    datasets = ["netmera-developer-guide", "netmera-user-guide", 
               "netmera-developer-guide-en", "netmera-user-guide-en"]
    
    timestamp = datetime.now().strftime("%Y%m%d")
    
    for dataset in datasets:
        experiment_name = f"daily_eval_{dataset}_{timestamp}"
        
        try:
            results = await run_evaluation(evaluator, dataset, experiment_name)
            print(f"✅ {dataset} evaluation completed")
        except Exception as e:
            print(f"❌ {dataset} evaluation failed: {e}")
    
    # Report oluştur
    reporter = EvaluationReporter()
    recent_experiments = reporter.get_recent_experiments(1)
    
    if recent_experiments:
        reports = reporter.generate_comprehensive_report(recent_experiments)
        print(f"📊 Daily report generated: {reports['html']}")

# Schedule daily evaluation
schedule.every().day.at("09:00").do(lambda: asyncio.run(daily_evaluation()))

# Run scheduler
while True:
    schedule.run_pending()
    time.sleep(3600)  # Check every hour
""")


def demo_ci_cd_integration():
    """CI/CD integration demo'su"""
    print("\n📚 DEMO 7: CI/CD Integration")
    print("=" * 50)
    
    print("""
# .github/workflows/evaluation.yml
name: Chatbot Evaluation

on:
  push:
    branches: [ main ]
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM

jobs:
  evaluate:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Setup evaluation
      run: |
        python setup_evaluation.py
      env:
        LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    
    - name: Run evaluation
      run: |
        python evaluate_chatbot.py --dataset all --experiment ci_cd_${{ github.sha }}
      env:
        LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
        OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
    
    - name: Generate reports
      run: |
        python -m src.evaluation.reporting --recent 1 --output ci_cd_report
      env:
        LANGSMITH_API_KEY: ${{ secrets.LANGSMITH_API_KEY }}
    
    - name: Upload reports
      uses: actions/upload-artifact@v3
      with:
        name: evaluation-reports
        path: evaluation_reports/
""")


def main():
    """Ana demo function"""
    print("🎯 Netmera Chatbot LangSmith Evaluation System")
    print("Demo ve Kullanım Örnekleri")
    print("=" * 60)
    
    # Check if setup was run
    if not Path("evaluation.env").exists() and not os.getenv("LANGSMITH_API_KEY"):
        print("⚠️  Setup henüz tamamlanmamış!")
        print("   Önce 'python setup_evaluation.py' çalıştırın")
        print()
    
    demos = [
        ("Temel Kullanım", demo_basic_usage),
        ("Python API", demo_python_api), 
        ("Reporting ve Analiz", demo_reporting),
        ("Custom Evaluators", demo_custom_evaluators),
        ("Gelişmiş Analiz", demo_advanced_analysis),
        ("Automation Pipeline", demo_automation),
        ("CI/CD Integration", demo_ci_cd_integration)
    ]
    
    print("📋 Mevcut Demo'lar:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"   {i}. {name}")
    
    print("\n" + "="*60)
    
    try:
        choice = input("Hangi demo'yu görmek istiyorsunuz? (1-7, 'all' for all, Enter for all): ").strip()
        
        if choice == "" or choice.lower() == "all":
            # Tüm demo'ları çalıştır
            for name, demo_func in demos:
                demo_func()
        elif choice.isdigit() and 1 <= int(choice) <= len(demos):
            # Belirli demo'yu çalıştır
            name, demo_func = demos[int(choice) - 1]
            demo_func()
        else:
            print("❌ Geçersiz seçim!")
            return
            
    except KeyboardInterrupt:
        print("\n👋 Demo sonlandırıldı")
        return
    
    print("\n" + "="*60)
    print("🚀 Evaluation'ı başlatmak için:")
    print("   python evaluate_chatbot.py --dataset all")
    print("\n📚 Detaylı dokümantasyon:")
    print("   EVALUATION_README.md")
    print("\n🔗 LangSmith Dashboard:")
    print("   https://smith.langchain.com/")


if __name__ == "__main__":
    main()
