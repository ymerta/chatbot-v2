#!/usr/bin/env python3
"""
Netmera Chatbot Evaluation Runner Script

Bu script, Netmera chatbot'unun performansını LangSmith kullanarak değerlendirmek için kullanılır.

Kullanım:
    python evaluate_chatbot.py --dataset all
    python evaluate_chatbot.py --dataset netmera-developer-guide
    python evaluate_chatbot.py --dataset netmera-developer-guide --experiment my_experiment

Environment Variables:
    LANGSMITH_API_KEY: LangSmith API key'i (zorunlu)
    OPENAI_API_KEY: OpenAI API key'i (zorunlu)
    LANGSMITH_PROJECT: LangSmith proje adı (opsiyonel)
"""

import os
import sys
import argparse
import asyncio
from pathlib import Path
from datetime import datetime

# Proje kök dizinini Python path'ine ekle
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.evaluation.langsmith_evaluator import NetmeraEvaluator, run_evaluation


def check_environment():
    """Environment variables'ların varlığını kontrol et"""
    required_vars = ["LANGSMITH_API_KEY", "OPENAI_API_KEY"]
    missing_vars = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\nPlease set these variables and try again.")
        return False
    
    return True


def setup_datasets(evaluator: NetmeraEvaluator) -> dict:
    """Dataset'leri setup et ve mevcut olanları döndür"""
    print("📦 Setting up evaluation datasets...")
    
    dataset_configs = {
        "netmera-developer-guide": {
            "file": "netmera_developer_guide_dataset.json",
            "description": "Netmera Developer Guide dataset'i - kapsamlı API, platform desteği, troubleshooting"
        },
        "netmera-user-guide": {
            "file": "netmera_user_guide_dataset.json",
            "description": "Netmera User Guide dataset'i - platform genel bakış, temel özellikler, kullanım"
        },
        "netmera-developer-guide-en": {
            "file": "netmera_developer_guide_dataset_en.json",
            "description": "Netmera Developer Guide dataset (English) - comprehensive API, platform support, troubleshooting"
        },
        "netmera-user-guide-en": {
            "file": "netmera_user_guide_dataset_en.json",
            "description": "Netmera User Guide dataset (English) - platform overview, basic features, usage"
        }
    }
    
    # Mevcut dataset'leri kontrol et
    existing_datasets = {ds.name: ds.id for ds in evaluator.list_datasets()}
    available_datasets = {}
    
    for name, config in dataset_configs.items():
        if name in existing_datasets:
            print(f"✅ Dataset exists: {name}")
            available_datasets[name] = existing_datasets[name]
        else:
            try:
                print(f"📁 Creating dataset: {name}")
                dataset_id = evaluator.create_dataset(
                    name,
                    config["file"], 
                    config["description"]
                )
                available_datasets[name] = dataset_id
            except Exception as e:
                print(f"⚠️  Failed to create dataset {name}: {e}")
    
    return available_datasets


async def run_single_evaluation(evaluator: NetmeraEvaluator, dataset_name: str, 
                               experiment_name: str = None) -> dict:
    """Tek bir dataset üzerinde evaluation çalıştır"""
    try:
        if not experiment_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            experiment_name = f"netmera_eval_{dataset_name}_{timestamp}"
        
        print(f"\n🚀 Starting evaluation...")
        print(f"   Dataset: {dataset_name}")
        print(f"   Experiment: {experiment_name}")
        
        results = await run_evaluation(evaluator, dataset_name, experiment_name)
        
        print(f"✅ Evaluation completed: {experiment_name}")
        print(f"📊 Results available at: https://smith.langchain.com/")
        
        return {
            "dataset": dataset_name,
            "experiment": experiment_name, 
            "status": "success",
            "results": results
        }
        
    except Exception as e:
        print(f"❌ Evaluation failed for {dataset_name}: {e}")
        return {
            "dataset": dataset_name,
            "experiment": experiment_name,
            "status": "failed",
            "error": str(e)
        }


async def main():
    """Ana function"""
    parser = argparse.ArgumentParser(
        description="Netmera Chatbot LangSmith Evaluation Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Örnekler:
  python evaluate_chatbot.py --dataset all
  python evaluate_chatbot.py --dataset netmera-developer-guide
  python evaluate_chatbot.py --dataset netmera-user-guide
  python evaluate_chatbot.py --dataset netmera-developer-guide-en
  python evaluate_chatbot.py --dataset netmera-user-guide-en
  python evaluate_chatbot.py --dataset netmera-developer-guide --experiment my_test
  python evaluate_chatbot.py --list-datasets
        """
    )
    
    parser.add_argument(
        "--dataset", 
        choices=["all", "netmera-developer-guide", "netmera-user-guide", 
                "netmera-developer-guide-en", "netmera-user-guide-en"],
        help="Evaluate edilecek dataset (all = tüm dataset'ler)"
    )
    
    parser.add_argument(
        "--experiment",
        help="Experiment adı (belirtilmezse otomatik oluşturulur)"
    )
    
    parser.add_argument(
        "--list-datasets",
        action="store_true",
        help="Mevcut dataset'leri listele ve çık"
    )
    
    parser.add_argument(
        "--project",
        default="netmera-chatbot-evaluation",
        help="LangSmith proje adı"
    )
    
    args = parser.parse_args()
    
    # Environment check
    if not check_environment():
        return 1
    
    try:
        # Evaluator'ı initialize et
        print("🤖 Initializing Netmera Chatbot Evaluator...")
        evaluator = NetmeraEvaluator(project_name=args.project)
        
        # Dataset'leri setup et
        available_datasets = setup_datasets(evaluator)
        
        if args.list_datasets:
            print(f"\n📋 Available datasets ({len(available_datasets)}):")
            for name in available_datasets:
                print(f"   - {name}")
            return 0
        
        if not args.dataset:
            print("\n❌ Please specify --dataset parameter")
            parser.print_help()
            return 1
        
        if not available_datasets:
            print("❌ No datasets available for evaluation")
            return 1
        
        # Evaluation'ları çalıştır
        evaluation_results = []
        
        if args.dataset == "all":
            print(f"\n🚀 Running evaluation on all {len(available_datasets)} datasets...")
            for dataset_name in available_datasets:
                result = await run_single_evaluation(
                    evaluator, 
                    dataset_name, 
                    f"{args.experiment}_{dataset_name}" if args.experiment else None
                )
                evaluation_results.append(result)
        else:
            if args.dataset not in available_datasets:
                print(f"❌ Dataset '{args.dataset}' not found")
                print(f"Available datasets: {list(available_datasets.keys())}")
                return 1
            
            result = await run_single_evaluation(
                evaluator,
                args.dataset,
                args.experiment
            )
            evaluation_results.append(result)
        
        # Sonuçları özetle
        print(f"\n📊 Evaluation Summary")
        print("=" * 50)
        
        successful = [r for r in evaluation_results if r["status"] == "success"]
        failed = [r for r in evaluation_results if r["status"] == "failed"]
        
        print(f"✅ Successful evaluations: {len(successful)}")
        print(f"❌ Failed evaluations: {len(failed)}")
        
        if successful:
            print(f"\n🎉 Successfully completed experiments:")
            for result in successful:
                print(f"   - {result['experiment']} (Dataset: {result['dataset']})")
        
        if failed:
            print(f"\n💥 Failed experiments:")
            for result in failed:
                print(f"   - {result['dataset']}: {result['error']}")
        
        print(f"\n🔗 View results at: https://smith.langchain.com/")
        print(f"📁 Project: {args.project}")
        
        return 0 if not failed else 1
        
    except KeyboardInterrupt:
        print("\n⚠️  Evaluation interrupted by user")
        return 130
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
