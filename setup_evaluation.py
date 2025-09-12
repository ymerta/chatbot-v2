#!/usr/bin/env python3
"""
Netmera Chatbot Evaluation Setup Script
Bu script, evaluation sistemini kurmanızı kolaylaştırır.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict


def check_requirements() -> List[str]:
    """Gerekli dosya ve klasörlerin varlığını kontrol et"""
    issues = []
    
    # Required files
    required_files = [
        "EvaluationDB/netmera_developer_guide_dataset.json",
        "EvaluationDB/netmera_user_guide_dataset.json",
        "EvaluationDB/netmera_developer_guide_dataset_en.json",
        "EvaluationDB/netmera_user_guide_dataset_en.json",
        "data/embeddings/faiss_store/index.faiss",
        "data/embeddings/faiss_store/index.pkl",
        "src/evaluation/langsmith_evaluator.py",
        "src/evaluation/config.py",
        "src/evaluation/reporting.py"
    ]
    
    for file_path in required_files:
        if not Path(file_path).exists():
            issues.append(f"Missing file: {file_path}")
    
    return issues


def check_environment_variables() -> List[str]:
    """Environment variables'ları kontrol et"""
    issues = []
    
    required_vars = ["OPENAI_API_KEY"]
    recommended_vars = ["LANGSMITH_API_KEY"]
    
    for var in required_vars:
        if not os.getenv(var):
            issues.append(f"Missing required environment variable: {var}")
    
    for var in recommended_vars:
        if not os.getenv(var):
            issues.append(f"Missing recommended environment variable: {var}")
    
    return issues


def check_python_packages() -> List[str]:
    """Python paketlerinin varlığını kontrol et"""
    issues = []
    
    required_packages = [
        "langsmith",
        "langchain",
        "langgraph", 
        "langchain_openai",
        "streamlit",
        "faiss_cpu",
        "pandas",
        "matplotlib",
        "seaborn"
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            issues.append(f"Missing Python package: {package}")
    
    return issues


def validate_datasets() -> List[str]:
    """Dataset dosyalarının format ve içeriğini kontrol et"""
    issues = []
    
    dataset_files = [
        "EvaluationDB/netmera_developer_guide_dataset.json",
        "EvaluationDB/netmera_user_guide_dataset.json",
        "EvaluationDB/netmera_developer_guide_dataset_en.json",
        "EvaluationDB/netmera_user_guide_dataset_en.json"
    ]
    
    for file_path in dataset_files:
        path = Path(file_path)
        if not path.exists():
            continue
            
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                issues.append(f"{file_path}: Should be a JSON array")
                continue
            
            if len(data) == 0:
                issues.append(f"{file_path}: Empty dataset")
                continue
                
            # Check first item structure
            first_item = data[0]
            if "inputs" not in first_item or "outputs" not in first_item:
                issues.append(f"{file_path}: Missing 'inputs' or 'outputs' in examples")
            
        except json.JSONDecodeError as e:
            issues.append(f"{file_path}: Invalid JSON format - {e}")
        except Exception as e:
            issues.append(f"{file_path}: Error reading file - {e}")
    
    return issues


def test_chatbot_initialization() -> List[str]:
    """Chatbot'un başlatılabilir olduğunu test et"""
    issues = []
    
    try:
        # Test basic imports
        from src.graph.app_graph import build_app_graph
        from src.config import FAISS_STORE_PATH
        from langchain_community.vectorstores import FAISS
        from langchain_openai import OpenAIEmbeddings
        
        # Test FAISS loading
        emb = OpenAIEmbeddings()
        vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
        
        # Test graph building
        docs = vs.docstore._dict
        corpus_texts = [d.page_content for d in docs.values()]
        corpus_meta = [d.metadata for d in docs.values()]
        
        graph = build_app_graph(corpus_texts, corpus_meta)
        
        print("✅ Chatbot initialization test passed")
        
    except ImportError as e:
        issues.append(f"Import error: {e}")
    except Exception as e:
        issues.append(f"Chatbot initialization error: {e}")
    
    return issues


def create_env_file():
    """evaluation.env dosyasını oluştur"""
    env_file = Path("evaluation.env")
    example_file = Path("evaluation.env.example")
    
    if env_file.exists():
        response = input("evaluation.env already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            return
    
    if example_file.exists():
        # Copy from example
        with open(example_file, 'r') as f:
            content = f.read()
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Created {env_file} from example")
        print("⚠️  Please edit evaluation.env and add your API keys!")
    else:
        # Create basic version
        content = """# Netmera Chatbot LangSmith Evaluation Environment
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=netmera-chatbot-evaluation
OPENAI_API_KEY=your_openai_api_key_here
CHAT_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-large
"""
        
        with open(env_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Created basic {env_file}")
        print("⚠️  Please edit evaluation.env and add your real API keys!")


def test_evaluation_system():
    """Evaluation sisteminin çalışabilirliğini test et"""
    print("🧪 Testing evaluation system...")
    
    try:
        from src.evaluation.config import validate_config, print_config_status
        
        errors = validate_config()
        if errors:
            print("❌ Configuration validation failed:")
            for error in errors:
                print(f"   - {error}")
            return False
        
        print("✅ Configuration validation passed")
        
        # Test evaluator import
        from src.evaluation import NetmeraEvaluator
        print("✅ Evaluator import successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Evaluation system test failed: {e}")
        return False


def run_quick_test():
    """Hızlı evaluation testi çalıştır"""
    response = input("Run a quick evaluation test? (y/N): ")
    if response.lower() != 'y':
        return
    
    print("🚀 Running quick evaluation test...")
    
    try:
        from src.evaluation import NetmeraEvaluator
        
        # API key kontrolü
        if not os.getenv("LANGSMITH_API_KEY"):
            print("❌ LANGSMITH_API_KEY not set, skipping test")
            return
        
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ OPENAI_API_KEY not set, skipping test")
            return
        
        evaluator = NetmeraEvaluator()
        
        # Dataset listesi
        datasets = evaluator.list_datasets()
        print(f"✅ Found {len(datasets)} existing datasets")
        
        # Test prediction
        test_input = {"question": "Netmera nedir?"}
        result = evaluator.chatbot_predictor(test_input)
        
        if result.get("answer"):
            print("✅ Chatbot prediction test passed")
            print(f"   Answer: {result['answer'][:100]}...")
        else:
            print("❌ Chatbot prediction test failed")
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")


def main():
    """Ana setup function"""
    print("🚀 Netmera Chatbot Evaluation Setup")
    print("=" * 50)
    
    all_issues = []
    
    # 1. Requirements check
    print("\n1️⃣ Checking requirements...")
    issues = check_requirements()
    if issues:
        print("❌ Missing files:")
        for issue in issues:
            print(f"   - {issue}")
        all_issues.extend(issues)
    else:
        print("✅ All required files present")
    
    # 2. Python packages check
    print("\n2️⃣ Checking Python packages...")
    issues = check_python_packages()
    if issues:
        print("❌ Missing packages:")
        for issue in issues:
            print(f"   - {issue}")
        print("\nRun: pip install -r requirements.txt")
        all_issues.extend(issues)
    else:
        print("✅ All required packages installed")
    
    # 3. Environment variables check
    print("\n3️⃣ Checking environment variables...")
    issues = check_environment_variables()
    if issues:
        print("⚠️  Environment issues:")
        for issue in issues:
            print(f"   - {issue}")
        
        # Offer to create env file
        if not Path("evaluation.env").exists():
            create_env_file()
        
        all_issues.extend(issues)
    else:
        print("✅ Environment variables configured")
    
    # 4. Dataset validation
    print("\n4️⃣ Validating datasets...")
    issues = validate_datasets()
    if issues:
        print("❌ Dataset issues:")
        for issue in issues:
            print(f"   - {issue}")
        all_issues.extend(issues)
    else:
        print("✅ All datasets valid")
    
    # 5. Chatbot initialization test
    print("\n5️⃣ Testing chatbot initialization...")
    issues = test_chatbot_initialization()
    if issues:
        print("❌ Chatbot issues:")
        for issue in issues:
            print(f"   - {issue}")
        all_issues.extend(issues)
    
    # 6. Evaluation system test
    print("\n6️⃣ Testing evaluation system...")
    if test_evaluation_system():
        print("✅ Evaluation system ready")
    else:
        all_issues.append("Evaluation system test failed")
    
    # Summary
    print("\n" + "=" * 50)
    if all_issues:
        print(f"❌ Setup incomplete - {len(all_issues)} issues found")
        print("\nNext steps:")
        print("1. Fix the issues listed above")
        print("2. Set your API keys in evaluation.env")
        print("3. Re-run this setup script")
    else:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Set your API keys in evaluation.env")
        print("2. Run evaluation: python evaluate_chatbot.py --dataset all")
        print("3. Check results at: https://smith.langchain.com/")
        
        # Optional quick test
        run_quick_test()
    
    print(f"\n📚 Documentation: EVALUATION_README.md")
    
    return len(all_issues) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
