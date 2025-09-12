"""
LangSmith Evaluation System for Netmera Chatbot
Bu modül, Netmera chatbot'unun performansını LangSmith kullanarak değerlendirmek için tasarlanmıştır.
"""

import os
import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime

from langsmith import Client
from langsmith.evaluation import evaluate
from langsmith.schemas import Run, Example
from langchain_core.messages import HumanMessage, AIMessage

# Import chatbot components
from src.graph.app_graph import build_app_graph
from src.config import FAISS_STORE_PATH, DATA_DIR
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings


class NetmeraEvaluator:
    """Netmera chatbot için LangSmith evaluation sistemi"""
    
    def __init__(self, api_key: Optional[str] = None, project_name: str = "netmera-chatbot-evaluation"):
        """
        Initialize evaluator
        
        Args:
            api_key: LangSmith API key (LANGSMITH_API_KEY environment variable'dan alınabilir)
            project_name: LangSmith projesi adı
        """
        self.client = Client(api_key=api_key)
        self.project_name = project_name
        self.base_dir = Path(__file__).parent.parent.parent
        
        # Chatbot'u initialize et
        self._initialize_chatbot()
        
    def _initialize_chatbot(self):
        """Chatbot components'lerini initialize et"""
        try:
            # FAISS store'dan dokümanları yükle
            emb = OpenAIEmbeddings()
            vs = FAISS.load_local(FAISS_STORE_PATH, emb, allow_dangerous_deserialization=True)
            docs = vs.docstore._dict
            
            corpus_texts = []
            corpus_meta = []
            for _id, d in docs.items():
                corpus_texts.append(d.page_content)
                corpus_meta.append(d.metadata)
            
            # Graph'ı compile et
            self.graph = build_app_graph(corpus_texts, corpus_meta)
            print("✅ Chatbot successfully initialized")
            
        except Exception as e:
            print(f"❌ Error initializing chatbot: {e}")
            raise
    
    def create_dataset(self, dataset_name: str, dataset_file: str, description: str = "") -> str:
        """
        LangSmith'te yeni dataset oluştur
        
        Args:
            dataset_name: Dataset adı
            dataset_file: JSON dataset dosyası yolu (EvaluationDB klasöründe)
            description: Dataset açıklaması
            
        Returns:
            Dataset ID
        """
        try:
            # Dataset dosyasını yükle
            dataset_path = self.base_dir / "EvaluationDB" / dataset_file
            with open(dataset_path, 'r', encoding='utf-8') as f:
                examples_data = json.load(f)
            
            # Dataset oluştur
            dataset = self.client.create_dataset(
                dataset_name=dataset_name,
                description=description or f"Netmera chatbot evaluation dataset from {dataset_file}"
            )
            
            # Examples'ları hazırla
            examples = []
            for item in examples_data:
                if "inputs" in item and "outputs" in item:
                    # LangSmith format (netmera_chatbot_dataset.json)
                    examples.append({
                        "inputs": item["inputs"],
                        "outputs": item["outputs"],
                        "metadata": item.get("metadata", {})
                    })
                elif "messages" in item.get("inputs", {}):
                    # Chat format (netmera_chat_dataset.json)
                    examples.append({
                        "inputs": {"messages": item["inputs"]["messages"]},
                        "outputs": {"messages": item["outputs"]["messages"]},
                        "metadata": item.get("metadata", {})
                    })
            
            # Examples'ları dataset'e ekle
            created_examples = self.client.create_examples(
                dataset_id=dataset.id,
                examples=examples
            )
            
            print(f"✅ Dataset '{dataset_name}' created with {len(examples)} examples")
            print(f"📊 Dataset ID: {dataset.id}")
            return dataset.id
            
        except Exception as e:
            print(f"❌ Error creating dataset: {e}")
            raise
    
    def list_datasets(self) -> List[Dict]:
        """Mevcut dataset'leri listele"""
        try:
            datasets = list(self.client.list_datasets())
            print(f"📋 Found {len(datasets)} datasets:")
            for ds in datasets:
                print(f"  - {ds.name} (ID: {ds.id})")
            return datasets
        except Exception as e:
            print(f"❌ Error listing datasets: {e}")
            return []
    
    def chatbot_predictor(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chatbot prediction function for LangSmith evaluation
        
        Args:
            inputs: Input dictionary containing question or messages
            
        Returns:
            Dictionary with chatbot response
        """
        try:
            # Handle different input formats
            if "question" in inputs:
                # Simple Q&A format
                question = inputs["question"]
            elif "messages" in inputs:
                # Chat format - get last user message
                messages = inputs["messages"]
                question = next((msg["content"] for msg in reversed(messages) if msg["role"] == "user"), "")
            else:
                raise ValueError("Invalid input format: expected 'question' or 'messages'")
            
            # Get chatbot response
            result = self.graph.invoke({"query": question})
            
            return {
                "answer": result.get("answer", ""),
                "citations": result.get("citations", []),
                "suggestions": result.get("suggestions", []),
                "retrieval_confidence": result.get("retrieval_conf", 0.0),
                "language": result.get("lang", "Unknown")
            }
            
        except Exception as e:
            print(f"❌ Error in chatbot predictor: {e}")
            return {"answer": f"Error: {str(e)}", "citations": [], "suggestions": []}


def accuracy_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """
    Enhanced Netmera-specific accuracy evaluator
    Teknik doğruluk ve Netmera bilgisi değerlendirmesi
    """
    try:
        prediction = run.outputs.get("answer", "").lower()
        original_answer = run.outputs.get("answer", "")
        
        # Temel doğruluk kontrolleri
        score = 0.2  # 🔧 BASELINE SCORE for any valid response
        feedback = []
        
        # 1. Boş cevap kontrolü
        if not prediction.strip():
            return {"key": "accuracy", "score": 0.0, "reason": "Empty response"}
        
        # 2. Error response kontrolü
        if "error" in prediction or "yeterli bilgi bulunamadı" in prediction or "there is no relevant information" in prediction:
            return {"key": "accuracy", "score": 0.1, "reason": "Error or insufficient information response"}
        
        feedback.append("Geçerli cevap")
        
        # 3. Enhanced Netmera terminology check (MORE COMPREHENSIVE)
        netmera_terms = {
            "platform": ["push notification", "push bildirim", "itme bildirim", "notification", "bildirim", "netmera"],
            "segmentation": ["segment", "segmentasyon", "kullanıcı segment", "hedef kitle", "target"],
            "campaign": ["kampanya", "campaign", "mesaj", "message"],
            "development": ["sdk", "api", "gradle", "implementation", "kod", "code", "setup", "kurulum"],
            "analytics": ["analytics", "analitik", "report", "rapor", "dashboard", "panel"],
            "automation": ["automation", "otomasyon", "journey", "akış"],
            "settings": ["settings", "ayar", "configuration", "yapılandırma", "general", "genel", "category", "kategori"],
            "ecommerce": ["ecommerce", "e-commerce", "commerce", "media", "catalog", "senaryolar"]
        }
        
        terms_used = 0
        for category, terms in netmera_terms.items():
            if any(term in prediction for term in terms):
                terms_used += 1
                
        if terms_used >= 1:
            score += 0.25
            feedback.append(f"Netmera terimleri kullanıldı ({terms_used} kategori)")
        
        # 4. Content structure and organization (SIMPLIFIED)
        structure_bonus = 0
        if any(indicator in prediction for indicator in ["1.", "2.", "3.", "adım", "step"]):
            structure_bonus += 0.15
            feedback.append("Yapılandırılmış açıklama")
        
        if any(indicator in prediction for indicator in ["**", "###", "##"]):
            structure_bonus += 0.10
            feedback.append("İyi formatlanmış")
            
        score += min(structure_bonus, 0.25)  # Max 0.25 for structure
        
        # 5. Technical detail and code examples (enhanced)
        tech_indicators = ["kod", "code", "gradle", "manifest", "json", "api key", "implementation", "xml", "```", "curl"]
        code_quality = 0
        for indicator in tech_indicators:
            if indicator in prediction:
                code_quality += 1
                
        if code_quality >= 1:
            if code_quality >= 3:
                score += 0.25  # Rich technical content
                feedback.append("Zengin teknik içerik")
            else:
                score += 0.15
                feedback.append("Teknik detaylar içeriyor")
        
        # 6. Helpful and informative content (EXPANDED)
        helpful_indicators = [
            "öner", "recommend", "suggest", "dikkat", "not", "important", "ipucu", "tip",
            "şu şekilde", "yapıp", "oluştur", "değiştir", "seç", "gir", "tıkla", "kullan",
            "erişim", "bul", "git", "başla", "açıkla", "göster", "belirt", "enable", "configure"
        ]
        if any(helpful in prediction for helpful in helpful_indicators):
            score += 0.15
            feedback.append("Faydalı açıklama var")
        
        # 7. Language quality and structure bonus
        if len(original_answer) > 200:  # Substantial answer
            score += 0.05
            feedback.append("Kapsamlı cevap")
            
        # 8. Netmera-specific context usage (EXPANDED)
        context_terms = [
            "dashboard", "panel", "settings", "configuration", "setup", "kurulum",
            "ayar", "seçenek", "menü", "ekran", "sayfa", "bölüm", "alan", "kategori",
            "platform", "uygulama", "sistem", "ara"
        ]
        if any(context_term in prediction for context_term in context_terms):
            score += 0.1
            feedback.append("Platform bağlamı kullanıldı")
        
        return {
            "key": "accuracy",
            "score": min(score, 1.0),
            "reason": "; ".join(feedback) if feedback else "Basic response"
        }
        
    except Exception as e:
        return {"key": "accuracy", "score": 0.0, "reason": f"Evaluator error: {str(e)}"}


def completeness_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """
    Cevapların kapsamlılık değerlendirmesi
    """
    try:
        prediction = run.outputs.get("answer", "")
        
        score = 0.0
        feedback = []
        
        # Minimum uzunluk kontrolü
        if len(prediction) < 50:
            return {"key": "completeness", "score": 0.2, "reason": "Too short response"}
        
        # Kapsamlılık kontrolleri
        completeness_indicators = [
            ("detaylı açıklama", ["detay", "detail", "açıklama", "explanation"], 0.2),
            ("adımlar", ["adım", "step", "1)", "2)", "3)"], 0.2),
            ("örnekler", ["örnek", "example", "mesela", "for instance"], 0.2),
            ("uyarılar", ["dikkat", "önemli", "not", "warning", "important"], 0.2),
            ("alternatifler", ["alternatif", "alternative", "diğer", "other", "veya", "or"], 0.2)
        ]
        
        for indicator_name, keywords, points in completeness_indicators:
            if any(keyword in prediction.lower() for keyword in keywords):
                score += points
                feedback.append(f"{indicator_name} var")
        
        return {
            "key": "completeness",
            "score": min(score, 1.0),
            "reason": "; ".join(feedback) if feedback else "Basic completeness"
        }
        
    except Exception as e:
        return {"key": "completeness", "score": 0.0, "reason": f"Evaluator error: {str(e)}"}


def helpfulness_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """
    Enhanced kullanıcı için faydalılık değerlendirmesi
    """
    try:
        prediction = run.outputs.get("answer", "").lower()
        original_answer = run.outputs.get("answer", "")
        
        score = 0.0
        feedback = []
        
        # Simplified faydalılık kontrolleri
        helpfulness_indicators = [
            ("actionable_steps", ["yapın", "tıklayın", "seçin", "girin", "ekleyin", "click", "select", "add", "configure"], 0.25),
            ("problem_solving", ["çözüm", "solution", "fix", "resolve", "sorun", "problem", "hata"], 0.25),
            ("practical_tips", ["ipucu", "tip", "öneri", "tavsiye", "recommend", "suggest"], 0.25),
            ("examples", ["örnek", "example", "mesela", "for instance", "örneğin"], 0.25)
        ]
        
        for indicator_name, keywords, max_points in helpfulness_indicators:
            keyword_count = sum(1 for keyword in keywords if keyword in prediction)
            if keyword_count > 0:
                # Award points based on frequency (more keywords = more helpful)
                points = min(max_points, max_points * (keyword_count / len(keywords)) * 2)
                score += points
                feedback.append(f"{indicator_name} ({keyword_count} indicator)")
        
        # Bonus for comprehensive answers
        if len(original_answer) > 300:
            score += 0.05
            feedback.append("Kapsamlı açıklama")
            
        # Bonus for code examples
        if any(code_indicator in original_answer for code_indicator in ["```", "gradle", "json", "xml", "implementation"]):
            score += 0.1
            feedback.append("Kod örnekleri")
            
        # Bonus for proper formatting (structured answer)
        if "**" in original_answer:  # Bold formatting
            score += 0.05
            feedback.append("İyi formatlanmış")
            
        # Penalty for vague responses
        vague_indicators = ["genel", "genellikle", "usually", "typically", "belki", "maybe"]
        vague_count = sum(1 for indicator in vague_indicators if indicator in prediction)
        if vague_count > 2:
            score -= 0.1
            feedback.append("Belirsiz ifadeler")
        
        return {
            "key": "helpfulness",
            "score": max(0.0, min(score, 1.0)),  # Ensure score is between 0 and 1
            "reason": "; ".join(feedback) if feedback else "Basic helpfulness"
        }
        
    except Exception as e:
        return {"key": "helpfulness", "score": 0.0, "reason": f"Evaluator error: {str(e)}"}


def language_consistency_evaluator(run: Run, example: Example) -> Dict[str, Any]:
    """
    Dil tutarlılığı değerlendirmesi
    """
    try:
        prediction = run.outputs.get("answer", "")
        language = run.outputs.get("language", "Unknown")
        
        # Türkçe karakter kontrolü
        turkish_chars = set("çğıöşü")
        has_turkish = any(char in prediction.lower() for char in turkish_chars)
        
        # İngilizce kelime yoğunluğu
        english_words = ["the", "and", "or", "with", "from", "that", "this", "you", "can", "will"]
        english_density = sum(1 for word in english_words if word in prediction.lower()) / max(len(prediction.split()), 1)
        
        score = 1.0
        reason = "Language consistent"
        
        # Karışık dil kullanımı cezası
        if has_turkish and english_density > 0.1:
            score = 0.7
            reason = "Mixed language usage"
        elif language == "Unknown":
            score = 0.8
            reason = "Language detection failed"
        
        return {
            "key": "language_consistency",
            "score": score,
            "reason": reason
        }
        
    except Exception as e:
        return {"key": "language_consistency", "score": 0.0, "reason": f"Evaluator error: {str(e)}"}


async def run_evaluation(evaluator: NetmeraEvaluator, dataset_name: str, 
                        experiment_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Evaluation'ı çalıştır
    
    Args:
        evaluator: NetmeraEvaluator instance
        dataset_name: Evaluate edilecek dataset adı
        experiment_name: Experiment adı (None ise otomatik oluşturulur)
    
    Returns:
        Evaluation sonuçları
    """
    if not experiment_name:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_name = f"netmera_eval_{timestamp}"
    
    print(f"🚀 Starting evaluation: {experiment_name}")
    print(f"📊 Dataset: {dataset_name}")
    
    try:
        # Evaluation'ı çalıştır
        results = await evaluate(
            evaluator.chatbot_predictor,
            data=dataset_name,
            evaluators=[
                accuracy_evaluator,
                completeness_evaluator,
                helpfulness_evaluator,
                language_consistency_evaluator
            ],
            experiment_prefix=experiment_name,
            description=f"Netmera chatbot evaluation on {dataset_name}",
            metadata={
                "model": "gpt-4o",
                "dataset": dataset_name,
                "evaluation_date": datetime.now().isoformat(),
                "evaluator_version": "1.0"
            }
        )
        
        print(f"✅ Evaluation completed: {experiment_name}")
        return results
        
    except Exception as e:
        print(f"❌ Evaluation error: {e}")
        raise


def main():
    """Ana evaluation runner"""
    print("🤖 Netmera Chatbot LangSmith Evaluation")
    print("=" * 50)
    
    # Environment variables kontrolü
    if not os.getenv("LANGSMITH_API_KEY"):
        print("⚠️  LANGSMITH_API_KEY environment variable not set!")
        print("   Please set it with your LangSmith API key")
        return
    
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY environment variable not set!")
        print("   Please set it with your OpenAI API key")
        return
    
    try:
        # Evaluator'ı initialize et
        evaluator = NetmeraEvaluator()
        
        # Mevcut dataset'leri listele
        print("\n📋 Existing datasets:")
        datasets = evaluator.list_datasets()
        
        # Dataset'leri oluştur (eğer yoksa)
        dataset_configs = [
            {
                "name": "netmera-basic-qa",
                "file": "netmera_chatbot_dataset.json",
                "description": "Temel Netmera Q&A dataset'i - genel özellikler ve kullanım senaryoları"
            },
            {
                "name": "netmera-advanced-qa", 
                "file": "netmera_extended_dataset.json",
                "description": "Gelişmiş Netmera Q&A dataset'i - teknik detaylar ve troubleshooting"
            },
            {
                "name": "netmera-chat-scenarios",
                "file": "netmera_chat_dataset.json", 
                "description": "Netmera chat senaryoları - multi-turn konuşmalar"
            }
        ]
        
        created_datasets = []
        existing_dataset_names = [ds.name for ds in datasets]
        
        for config in dataset_configs:
            if config["name"] not in existing_dataset_names:
                print(f"\n📦 Creating dataset: {config['name']}")
                dataset_id = evaluator.create_dataset(
                    config["name"], 
                    config["file"], 
                    config["description"]
                )
                created_datasets.append(config["name"])
            else:
                print(f"✅ Dataset already exists: {config['name']}")
                created_datasets.append(config["name"])
        
        # Evaluation'ları çalıştır
        print(f"\n🚀 Running evaluations on {len(created_datasets)} datasets...")
        
        for dataset_name in created_datasets:
            print(f"\n📊 Evaluating: {dataset_name}")
            asyncio.run(run_evaluation(evaluator, dataset_name))
        
        print("\n✅ All evaluations completed!")
        print("🔗 Check results at: https://smith.langchain.com/")
        
    except Exception as e:
        print(f"❌ Main execution error: {e}")
        raise


if __name__ == "__main__":
    main()
