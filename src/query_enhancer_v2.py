"""
Enhanced Query Processing for Better Retrieval
Addresses the platform query issues with a simple, effective approach
"""

import re
from typing import List, Dict, Tuple, Any

class QueryEnhancer:
    """Enhanced query processing to improve retrieval accuracy"""
    
    def __init__(self):
        # Query expansion patterns (platform-specific logic removed)
        self.expansion_patterns = {
            # Integration questions
            "integration": {
                "triggers": ["entegrasyon", "integration", "kurulum", "setup", "install", "implement", "nasıl"],
                "expansions": ["SDK setup", "implementation", "integration steps", "configuration"],
                "boost_sources": ["developer-guide", "getting-started"],
                "avoid_sources": ["api-documentation"]
            },
            
            # API questions
            "api": {
                "triggers": ["api", "endpoint", "request", "response", "documentation"],
                "expansions": ["REST API", "HTTP", "JSON", "authentication", "parameters"],
                "boost_sources": ["api-documentation", "rest-api"],
                "avoid_sources": ["user-guide"]
            },
            
            # Feature questions
            "features": {
                "triggers": ["özellik", "feature", "neler", "what", "capabilities"],
                "expansions": ["push notification", "analytics", "segmentation", "campaign", "automation"],
                "boost_sources": ["developer-guide", "features"],
                "avoid_sources": ["troubleshooting"]
            }
        }
    
    def detect_query_type(self, query: str) -> str:
        """Detect the type of query"""
        query_lower = query.lower()
        
        max_matches = 0
        detected_type = "general"
        
        for qtype, config in self.expansion_patterns.items():
            matches = sum(1 for trigger in config["triggers"] if trigger in query_lower)
            if matches > max_matches:
                max_matches = matches
                detected_type = qtype
        
        return detected_type if max_matches > 0 else "general"
    
    def expand_query(self, query: str) -> List[str]:
        """Expand query with related terms"""
        query_type = self.detect_query_type(query)
        
        expanded_queries = [query]  # Original query first
        
        if query_type in self.expansion_patterns:
            config = self.expansion_patterns[query_type]
            
            # Add expansions
            for expansion in config["expansions"]:
                expanded_queries.append(f"{query} {expansion}")
                
            # No platform-specific query generation
        
        return expanded_queries[:5]  # Limit to 5 queries
    
    def calculate_relevance_score(self, document_content: str, document_metadata: Dict, 
                                 original_query: str, query_type: str) -> float:
        """Calculate relevance score for reranking"""
        content_lower = document_content.lower()
        source = document_metadata.get("source", "").lower()
        
        score = 0.0
        
        # Base score from query terms in content
        query_terms = original_query.lower().split()
        term_matches = sum(1 for term in query_terms if term in content_lower)
        score += (term_matches / len(query_terms)) * 0.4
        
        # Type-specific scoring
        if query_type in self.expansion_patterns:
            config = self.expansion_patterns[query_type]
            
            # Boost if source is preferred for this query type
            for boost_source in config["boost_sources"]:
                if boost_source in source:
                    score += 0.3
                    break
            
            # Penalize if source should be avoided
            for avoid_source in config["avoid_sources"]:
                if avoid_source in source:
                    score -= 0.4
                    break
            
            # Boost if content contains expected terms
            expansion_matches = sum(1 for exp in config["expansions"] 
                                  if exp.lower() in content_lower)
            score += (expansion_matches / len(config["expansions"])) * 0.3
        
        # No special platform handling - use general patterns only
        
        return max(0.0, min(1.0, score))  # Clamp between 0 and 1
    
    def determine_optimal_k(self, query: str, query_type: str) -> int:
        """Determine optimal number of documents to retrieve"""
        base_k = 3
        
        # Increase K for complex queries
        if len(query.split()) > 5:
            base_k += 2
        
        # Increase K for feature questions
        if query_type == "features":
            base_k += 2
        
        # Increase K for integration questions (need multiple solutions)
        if query_type == "integration":
            base_k += 2
        
        return min(base_k, 10)  # Cap at 10
    
    def enhance_query_for_retrieval(self, query: str) -> Dict[str, Any]:
        """Main method to enhance query for better retrieval"""
        
        query_type = self.detect_query_type(query)
        expanded_queries = self.expand_query(query)
        optimal_k = self.determine_optimal_k(query, query_type)
        
        return {
            "original_query": query,
            "query_type": query_type,
            "expanded_queries": expanded_queries,
            "optimal_k": optimal_k,
            "enhancement_config": self.expansion_patterns.get(query_type, {})
        }
    
    def rerank_results(self, results: List[Tuple[Any, float]], 
                      query: str, query_type: str) -> List[Tuple[Any, float]]:
        """Rerank results based on relevance"""
        
        if not results:
            return results
        
        scored_results = []
        
        for doc, original_score in results:
            # Calculate custom relevance score
            relevance_score = self.calculate_relevance_score(
                doc.page_content, 
                doc.metadata, 
                query, 
                query_type
            )
            
            # Combine with original similarity score
            # Lower similarity score is better in FAISS, so invert it
            similarity_score = 1.0 / (1.0 + original_score)
            
            final_score = (relevance_score * 0.7) + (similarity_score * 0.3)
            
            scored_results.append((doc, final_score, original_score))
        
        # Sort by final score (higher is better)
        scored_results.sort(key=lambda x: x[1], reverse=True)
        
        # Return with original format
        return [(doc, original_score) for doc, _, original_score in scored_results]


# Integration function for existing chatbot
def enhance_chatbot_retrieval(vectorstore, query: str, debug: bool = False) -> List[Tuple[Any, float]]:
    """
    Enhanced retrieval function that can be integrated into existing chatbot
    
    Args:
        vectorstore: FAISS vectorstore instance
        query: User query
        debug: Whether to print debug information
        
    Returns:
        List of (document, score) tuples, reranked for better relevance
    """
    
    enhancer = QueryEnhancer()
    
    # Step 1: Enhance query
    enhancement = enhancer.enhance_query_for_retrieval(query)
    
    if debug:
        print(f"🔍 Original Query: {query}")
        print(f"🎯 Query Type: {enhancement['query_type']}")
        print(f"📊 Optimal K: {enhancement['optimal_k']}")
        print(f"📝 Expanded Queries: {len(enhancement['expanded_queries'])}")
    
    # Step 2: Search with multiple queries
    all_results = []
    seen_content = set()
    
    for expanded_query in enhancement['expanded_queries']:
        try:
            results = vectorstore.similarity_search_with_score(
                expanded_query, 
                k=enhancement['optimal_k']
            )
            
            for doc, score in results:
                # Use first 100 chars as unique identifier
                content_id = hash(doc.page_content[:100])
                
                if content_id not in seen_content:
                    seen_content.add(content_id)
                    all_results.append((doc, score))
                    
        except Exception as e:
            if debug:
                print(f"⚠️ Error with query '{expanded_query}': {e}")
            continue
    
    if debug:
        print(f"📥 Total unique results: {len(all_results)}")
    
    # Step 3: Rerank results
    final_results = enhancer.rerank_results(
        all_results, 
        query, 
        enhancement['query_type']
    )
    
    # Limit to reasonable number
    final_results = final_results[:enhancement['optimal_k']]
    
    if debug:
        print(f"🏆 Final results: {len(final_results)}")
        for i, (doc, score) in enumerate(final_results[:3]):
            source = doc.metadata.get("source", "unknown")[:50]
            print(f"   {i+1}. {source}... (score: {score:.3f})")
    
    return final_results


# Test function
def test_enhancement():
    """Test the enhancement with problematic queries"""
    
    enhancer = QueryEnhancer()
    
    test_queries = [
        "Netmera hangi platformları destekliyor?",
        "Netmera hangi platformları destekliyor developer",
        "iOS Android React Native support",
        "API documentation",
        "push notification setup"
    ]
    
    print("🧪 Testing Query Enhancement")
    print("=" * 50)
    
    for query in test_queries:
        enhancement = enhancer.enhance_query_for_retrieval(query)
        
        print(f"\n🔍 Query: {query}")
        print(f"   Type: {enhancement['query_type']}")
        print(f"   Optimal K: {enhancement['optimal_k']}")
        print(f"   Expansions: {enhancement['expanded_queries'][:2]}...")


if __name__ == "__main__":
    test_enhancement()
    
    print("\n💡 Integration Guide:")
    print("   1. Replace similarity_search_with_score calls with enhance_chatbot_retrieval")
    print("   2. Query expansion improves content discovery")
    print("   3. Results reranked based on content type and source relevance")
    print("   4. Dynamic K selection for integration/feature queries")
    
    print("\n🎯 This should solve:")
    print("   ✓ General query enhancement without platform-specific logic")
    print("   ✓ Better K selection for integration (K=5) and feature (K=5) queries")
    print("   ✓ Content-aware ranking for API, integration, and feature questions")
    print("   ✓ Query expansion for better content discovery")
