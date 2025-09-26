"""
Improved Retrieval System
Addresses query expansion, dynamic K selection, and better chunk ranking
"""

import re
from typing import List, Dict, Tuple, Any, Optional
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
import os

class ImprovedRetrievalSystem:
    """Enhanced retrieval system with query expansion and dynamic K selection"""
    
    def __init__(self, faiss_store_path: str = "data/embeddings/faiss_store"):
        self.faiss_store_path = faiss_store_path
        self.embeddings = OpenAIEmbeddings()
        self.llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
        self.vectorstore = None
        self.load_vectorstore()
        
        # Query patterns and their enhancements
        self.query_patterns = {
            "platform": {
                "keywords": ["platform", "platformları", "hangi", "destekliyor", "supports", "which"],
                "expansions": ["iOS", "Android", "React Native", "Flutter", "Unity", "Web", "mobile"],
                "context": "platform support and compatibility"
            },
            "integration": {
                "keywords": ["entegrasyon", "integration", "kurulum", "setup", "install", "implement"],
                "expansions": ["SDK", "setup", "configuration", "implementation", "steps"],
                "context": "integration and setup procedures"
            },
            "features": {
                "keywords": ["özellik", "feature", "neler", "what", "nasıl", "how"],
                "expansions": ["push notification", "analytics", "segmentation", "campaign", "automation"],
                "context": "features and capabilities"
            },
            "troubleshooting": {
                "keywords": ["hata", "error", "problem", "sorun", "çözüm", "fix", "solve"],
                "expansions": ["debug", "troubleshoot", "issue", "solution", "resolve"],
                "context": "troubleshooting and error resolution"
            },
            "api": {
                "keywords": ["api", "endpoint", "request", "response", "documentation"],
                "expansions": ["REST", "HTTP", "JSON", "authentication", "parameters"],
                "context": "API documentation and usage"
            }
        }
    
    def load_vectorstore(self):
        """Load FAISS vectorstore"""
        try:
            if os.path.exists(self.faiss_store_path):
                self.vectorstore = FAISS.load_local(
                    self.faiss_store_path, 
                    self.embeddings, 
                    allow_dangerous_deserialization=True
                )
                print(f"✅ FAISS vectorstore loaded from {self.faiss_store_path}")
            else:
                print(f"❌ FAISS vectorstore not found at {self.faiss_store_path}")
        except Exception as e:
            print(f"⚠️ Error loading vectorstore: {e}")
    
    def detect_query_intent(self, query: str) -> Dict[str, Any]:
        """Detect query intent and suggest enhancements"""
        query_lower = query.lower()
        detected_intents = []
        
        for intent, config in self.query_patterns.items():
            keyword_matches = sum(1 for keyword in config["keywords"] if keyword in query_lower)
            if keyword_matches > 0:
                detected_intents.append({
                    "intent": intent,
                    "confidence": keyword_matches / len(config["keywords"]),
                    "config": config
                })
        
        # Sort by confidence
        detected_intents.sort(key=lambda x: x["confidence"], reverse=True)
        
        return {
            "primary_intent": detected_intents[0] if detected_intents else None,
            "all_intents": detected_intents,
            "needs_expansion": len(detected_intents) > 0
        }
    
    def expand_query(self, query: str, intent_info: Dict) -> List[str]:
        """Expand query with related terms and context"""
        expanded_queries = [query]  # Original query
        
        if not intent_info["needs_expansion"]:
            return expanded_queries
        
        primary_intent = intent_info["primary_intent"]
        if not primary_intent:
            return expanded_queries
        
        config = primary_intent["config"]
        
        # Add expansions to original query
        for expansion in config["expansions"]:
            expanded_queries.append(f"{query} {expansion}")
        
        # Create context-specific queries
        context_query = f"{config['context']} {query}"
        expanded_queries.append(context_query)
        
        # Create more specific queries
        if "platform" in primary_intent["intent"]:
            platform_queries = [
                "Netmera supports which mobile platforms",
                "Netmera iOS Android React Native support",
                "supported platforms Netmera SDK"
            ]
            expanded_queries.extend(platform_queries)
        
        elif "integration" in primary_intent["intent"]:
            integration_queries = [
                "Netmera SDK integration steps",
                "how to implement Netmera",
                "Netmera setup guide"
            ]
            expanded_queries.extend(integration_queries)
        
        return expanded_queries[:6]  # Limit to 6 queries max
    
    def calculate_dynamic_k(self, query: str, intent_info: Dict) -> int:
        """Calculate dynamic K based on query complexity and intent"""
        base_k = 3
        
        # Increase K for complex queries
        if len(query.split()) > 5:
            base_k += 2
        
        # Increase K for platform questions (they often need multiple sources)
        if intent_info["primary_intent"] and "platform" in intent_info["primary_intent"]["intent"]:
            base_k += 3
        
        # Increase K for troubleshooting (need multiple solutions)
        if intent_info["primary_intent"] and "troubleshooting" in intent_info["primary_intent"]["intent"]:
            base_k += 2
        
        # Increase K for feature questions (need comprehensive coverage)
        if intent_info["primary_intent"] and "features" in intent_info["primary_intent"]["intent"]:
            base_k += 2
        
        return min(base_k, 10)  # Cap at 10
    
    def retrieve_with_multiple_queries(self, queries: List[str], k: int) -> List[Tuple[Any, float]]:
        """Retrieve documents using multiple query variations"""
        if not self.vectorstore:
            return []
        
        all_results = []
        seen_content = set()
        
        for query in queries:
            try:
                results = self.vectorstore.similarity_search_with_score(query, k=k)
                
                for doc, score in results:
                    content_hash = hash(doc.page_content[:200])  # Use first 200 chars as identifier
                    
                    if content_hash not in seen_content:
                        seen_content.add(content_hash)
                        all_results.append((doc, score, query))  # Include which query found it
                        
            except Exception as e:
                print(f"⚠️ Error in query '{query}': {e}")
                continue
        
        # Sort by score (lower is better for FAISS)
        all_results.sort(key=lambda x: x[1])
        
        return all_results[:k*2]  # Return up to 2*k results
    
    def rerank_results(self, results: List[Tuple[Any, float, str]], 
                      original_query: str, intent_info: Dict) -> List[Tuple[Any, float]]:
        """Rerank results based on content relevance and metadata"""
        if not results:
            return []
        
        scored_results = []
        
        for doc, original_score, found_by_query in results:
            content = doc.page_content.lower()
            metadata = doc.metadata
            
            # Start with original similarity score (invert so higher is better)
            relevance_score = 1.0 / (1.0 + original_score)
            
            # Boost based on intent matching
            if intent_info["primary_intent"]:
                intent = intent_info["primary_intent"]["intent"]
                
                if intent == "platform":
                    platform_terms = ["ios", "android", "react native", "flutter", "unity", "web", "mobile", "platform"]
                    platform_matches = sum(1 for term in platform_terms if term in content)
                    relevance_score += platform_matches * 0.3
                    
                    # Boost developer guide content for platform questions
                    if "developer" in metadata.get("source", "").lower():
                        relevance_score += 0.4
                
                elif intent == "integration":
                    integration_terms = ["setup", "install", "implement", "sdk", "integration", "kurulum"]
                    integration_matches = sum(1 for term in integration_terms if term in content)
                    relevance_score += integration_matches * 0.2
                
                elif intent == "features":
                    feature_terms = ["push", "notification", "analytics", "segment", "campaign", "automation"]
                    feature_matches = sum(1 for term in feature_terms if term in content)
                    relevance_score += feature_matches * 0.2
            
            # Boost based on content type
            content_type = metadata.get("content_type", "")
            if content_type == "api" and "api" in original_query.lower():
                relevance_score += 0.3
            elif content_type == "tutorial" and any(word in original_query.lower() for word in ["nasıl", "how", "adım", "step"]):
                relevance_score += 0.3
            
            # Boost enhanced chunks (they have better context)
            if metadata.get("enhancement_features", {}).get("is_enhanced", False):
                relevance_score += 0.2
            
            # Penalize if source doesn't seem relevant
            source = metadata.get("source", "").lower()
            if "platform" in original_query.lower() and "iys" in source:
                relevance_score -= 0.4  # IYS is not relevant for platform questions
            
            scored_results.append((doc, relevance_score, original_score, found_by_query))
        
        # Sort by relevance score (higher is better)
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return top results with original format
        return [(doc, original_score) for doc, _, original_score, _ in scored_results[:10]]
    
    def enhanced_retrieve(self, query: str, debug: bool = False) -> List[Tuple[Any, float]]:
        """Main enhanced retrieval method"""
        
        if debug:
            print(f"🔍 Original Query: {query}")
        
        # Step 1: Detect intent
        intent_info = self.detect_query_intent(query)
        
        if debug and intent_info["primary_intent"]:
            print(f"🎯 Detected Intent: {intent_info['primary_intent']['intent']} (confidence: {intent_info['primary_intent']['confidence']:.2f})")
        
        # Step 2: Expand query
        expanded_queries = self.expand_query(query, intent_info)
        
        if debug:
            print(f"📝 Expanded Queries ({len(expanded_queries)}):")
            for i, eq in enumerate(expanded_queries):
                print(f"   {i+1}. {eq}")
        
        # Step 3: Calculate dynamic K
        dynamic_k = self.calculate_dynamic_k(query, intent_info)
        
        if debug:
            print(f"📊 Dynamic K: {dynamic_k}")
        
        # Step 4: Retrieve with multiple queries
        raw_results = self.retrieve_with_multiple_queries(expanded_queries, dynamic_k)
        
        if debug:
            print(f"📥 Raw Results: {len(raw_results)} documents")
        
        # Step 5: Rerank results
        final_results = self.rerank_results(raw_results, query, intent_info)
        
        if debug:
            print(f"🏆 Final Results: {len(final_results)} documents")
            for i, (doc, score) in enumerate(final_results[:3]):
                source = doc.metadata.get("source", "unknown")
                content_preview = doc.page_content[:100].replace("\n", " ")
                print(f"   {i+1}. {source} (score: {score:.3f})")
                print(f"      Preview: {content_preview}...")
        
        return final_results
    
    def test_with_problematic_queries(self):
        """Test the system with queries that were problematic before"""
        
        test_queries = [
            "Netmera hangi platformları destekliyor?",
            "Netmera hangi platformları destekliyor developer",
            "iOS Android support Netmera",
            "React Native Netmera SDK",
            "mobile platform compatibility",
            "supported development platforms"
        ]
        
        print("🧪 Testing Improved Retrieval System")
        print("=" * 60)
        
        for query in test_queries:
            print(f"\n🔍 Query: {query}")
            print("-" * 40)
            
            results = self.enhanced_retrieve(query, debug=True)
            
            if results:
                best_result = results[0]
                source = best_result[0].metadata.get("source", "unknown")
                print(f"✅ Best Match: {source}")
                
                # Check if it's about platforms
                content = best_result[0].page_content.lower()
                has_platform_info = any(platform in content for platform in 
                                      ["ios", "android", "react native", "flutter", "platform"])
                
                if has_platform_info:
                    print("🎯 Contains platform information: YES")
                else:
                    print("❌ Contains platform information: NO")
            else:
                print("❌ No results found")
            
            print()


def integrate_improved_retrieval():
    """Integrate improved retrieval into existing system"""
    
    print("🔧 Integrating Improved Retrieval System...")
    
    # Test the system
    retrieval_system = ImprovedRetrievalSystem()
    
    if retrieval_system.vectorstore:
        print("✅ System ready for testing")
        
        # Run tests
        retrieval_system.test_with_problematic_queries()
        
        return retrieval_system
    else:
        print("❌ Could not load FAISS vectorstore")
        return None


if __name__ == "__main__":
    print("🚀 Improved Retrieval System")
    print("Addresses query expansion, dynamic K, and better ranking")
    print("=" * 60)
    
    system = integrate_improved_retrieval()
    
    if system:
        print("\n💡 Integration Points:")
        print("   1. 🔍 Query intent detection and expansion")
        print("   2. 📊 Dynamic K selection based on query complexity")
        print("   3. 🎯 Multi-query retrieval for better coverage")
        print("   4. 🏆 Smart reranking based on content relevance")
        print("   5. 📈 Metadata-aware scoring for better results")
        
        print("\n🎯 This should solve:")
        print("   ✓ Platform questions finding wrong documents")
        print("   ✓ Top K=3 limitation")
        print("   ✓ Query specificity issues")
        print("   ✓ Content ranking problems")
