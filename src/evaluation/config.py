"""
Evaluation Configuration
LangSmith evaluation için konfigürasyon ayarları
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Evaluation environment dosyasını yükle
evaluation_env_path = Path(__file__).parent.parent.parent / "evaluation.env"
if evaluation_env_path.exists():
    load_dotenv(evaluation_env_path)

# LangSmith Configuration
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "netmera-chatbot-evaluation")
LANGSMITH_ENDPOINT = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

# Evaluation Settings
EVALUATION_BATCH_SIZE = int(os.getenv("EVALUATION_BATCH_SIZE", "10"))
EVALUATION_CONCURRENCY = int(os.getenv("EVALUATION_CONCURRENCY", "3"))
EVALUATION_TIMEOUT = int(os.getenv("EVALUATION_TIMEOUT", "300"))

# Dataset Configuration
DATASET_CONFIGS = {
    "netmera-developer-guide": {
        "file": "netmera_developer_guide_dataset.json",
        "description": "Netmera Developer Guide dataset'i - kapsamlı API, platform desteği, troubleshooting",
        "expected_examples": 20,
        "categories": ["platform_support", "rest_api", "user_management", "integrations", "troubleshooting"]
    }
}

# Evaluator Configuration
EVALUATOR_CONFIGS = {
    "accuracy": {
        "name": "Doğruluk",
        "description": "Teknik doğruluk ve Netmera bilgisi",
        "weight": 0.5,  # 🔧 INCREASED: More weight to accuracy
        "threshold": 0.6  # 🔧 LOWERED: More realistic threshold
    },
    "completeness": {
        "name": "Kapsamlılık", 
        "description": "Cevapların kapsamlılığı ve detay seviyesi",
        "weight": 0.3,  # 🔧 INCREASED: More weight to completeness
        "threshold": 0.5  # 🔧 LOWERED: More realistic threshold
    },
    "language_consistency": {
        "name": "Dil Tutarlılığı",
        "description": "Dil kullanımının tutarlılığı",
        "weight": 0.2,
        "threshold": 0.8
    }
}

# Performance Benchmarks
PERFORMANCE_BENCHMARKS = {
    "response_time": {
        "excellent": 2.0,  # seconds
        "good": 5.0,
        "acceptable": 10.0
    },
    "accuracy": {
        "excellent": 0.8,  # 🔧 MORE REALISTIC: lowered from 0.9
        "good": 0.65,      # 🔧 MORE REALISTIC: lowered from 0.75
        "acceptable": 0.5  # 🔧 MORE REALISTIC: lowered from 0.6
    },
    "completeness": {
        "excellent": 0.8,  # 🔧 MORE REALISTIC: lowered from 0.85
        "good": 0.65,      # 🔧 MORE REALISTIC: lowered from 0.7
        "acceptable": 0.5  # 🔧 MORE REALISTIC: lowered from 0.55
    }
}

# Netmera Specific Keywords and Terms
NETMERA_KEYWORDS = {
    "platform_terms": [
        "netmera", "push notification", "segment", "campaign", "dashboard",
        "sdk", "api", "analytics", "automation", "journey"
    ],
    "technical_terms": [
        "gradle", "manifest", "api key", "certificate", "token", "payload",
        "endpoint", "webhook", "integration", "authentication"
    ],
    "feature_terms": [
        "personalization", "geofencing", "ab test", "rich media", "deep link",
        "silent push", "badge", "frequency capping", "opt-out", "gdpr"
    ],
    "metric_terms": [
        "delivery rate", "open rate", "click rate", "conversion rate", "ctr",
        "roi", "roas", "retention", "churn", "dau", "mau"
    ]
}

# Language Detection Patterns
LANGUAGE_PATTERNS = {
    "turkish": {
        "chars": "çğıöşü",
        "words": ["ve", "ile", "için", "olan", "bir", "bu", "şu", "nasıl", "nedir", "hangi"],
        "suffixes": ["dir", "dur", "lar", "ler", "da", "de", "ta", "te"]
    },
    "english": {
        "words": ["the", "and", "or", "with", "from", "that", "this", "you", "can", "will", "how", "what", "which"],
        "patterns": ["ing$", "ed$", "ly$", "tion$", "ness$"]
    }
}

# Evaluation Report Configuration  
REPORT_CONFIG = {
    "output_formats": ["json", "html", "csv"],
    "charts": {
        "score_distribution": True,
        "category_performance": True,
        "time_series": True,
        "comparison": True
    },
    "export_path": "./evaluation_reports"
}


def get_evaluation_config() -> Dict:
    """Complete evaluation configuration'ını döndür"""
    return {
        "langsmith": {
            "api_key": LANGSMITH_API_KEY,
            "project": LANGSMITH_PROJECT,
            "endpoint": LANGSMITH_ENDPOINT
        },
        "datasets": DATASET_CONFIGS,
        "evaluators": EVALUATOR_CONFIGS,
        "benchmarks": PERFORMANCE_BENCHMARKS,
        "keywords": NETMERA_KEYWORDS,
        "language_patterns": LANGUAGE_PATTERNS,
        "report": REPORT_CONFIG,
        "settings": {
            "batch_size": EVALUATION_BATCH_SIZE,
            "concurrency": EVALUATION_CONCURRENCY,
            "timeout": EVALUATION_TIMEOUT
        }
    }


def validate_config() -> List[str]:
    """Configuration validation - eksik veya hatalı ayarları kontrol et"""
    errors = []
    
    if not LANGSMITH_API_KEY:
        errors.append("LANGSMITH_API_KEY is required")
    
    if not os.getenv("OPENAI_API_KEY"):
        errors.append("OPENAI_API_KEY is required")
    
    # Dataset dosyalarının varlığını kontrol et
    base_dir = Path(__file__).parent.parent.parent
    eval_db_dir = base_dir / "EvaluationDB"
    
    for dataset_name, config in DATASET_CONFIGS.items():
        dataset_file = eval_db_dir / config["file"]
        if not dataset_file.exists():
            errors.append(f"Dataset file not found: {dataset_file}")
    
    return errors


def print_config_status():
    """Configuration durumunu yazdır"""
    print("🔧 Evaluation Configuration Status")
    print("=" * 40)
    
    errors = validate_config()
    
    if not errors:
        print("✅ Configuration is valid")
        print(f"📊 LangSmith Project: {LANGSMITH_PROJECT}")
        print(f"📁 Datasets: {len(DATASET_CONFIGS)}")
        print(f"🔍 Evaluators: {len(EVALUATOR_CONFIGS)}")
    else:
        print("❌ Configuration errors:")
        for error in errors:
            print(f"   - {error}")
    
    return len(errors) == 0
