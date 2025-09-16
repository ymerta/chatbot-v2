"""
Test script for GraphRAG integration
"""

import os
import sys
sys.path.append('src')

def test_graphrag_components():
    """Test individual GraphRAG components"""
    print("🔍 Testing GraphRAG components...")
    
    try:
        # Test graph store
        from src.graphrag.graph_store import NetmeraGraphStore
        
        print("1. Testing Graph Store...")
        graph_store = NetmeraGraphStore()
        
        # Build sample graph if empty
        if graph_store.graph.number_of_nodes() == 0:
            print("   Building sample graph...")
            graph_store.build_sample_graph()
        
        stats = graph_store.get_stats()
        print(f"   Graph stats: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
        
        # Test entity search
        entities = graph_store.search_entities("SDK", limit=3)
        print(f"   Found {len(entities)} SDK-related entities")
        
        # Test query router
        print("2. Testing Query Router...")
        from src.graphrag.query_router import QueryRouter
        
        router = QueryRouter()
        
        test_queries = [
            "Netmera SDK nasıl kurulur?",
            "Push notification nedir?",
            "iOS ve Android entegrasyonu nasıl yapılır?"
        ]
        
        for query in test_queries:
            routing_result = router.route_query(query)
            route_type = routing_result['route_type']
            strategy = routing_result['strategy']
            print(f"   Query: '{query}' -> {route_type.value} / {strategy.value} (graph: {routing_result['graph_score']:.2f}, vector: {routing_result['vector_score']:.2f})")
        
        # Test graph retriever
        print("3. Testing Graph Retriever...")
        from src.graphrag.graph_retriever import GraphRAGRetriever
        
        retriever = GraphRAGRetriever(graph_store)
        context = retriever.retrieve("Netmera SDK requirements", max_entities=3)
        print(f"   Retrieved {len(context.entities)} entities, confidence: {context.confidence:.2f}")
        
        print("✅ All GraphRAG components working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing GraphRAG: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_hybrid_retriever():
    """Test hybrid retriever with sample data"""
    print("\n🔗 Testing Hybrid GraphRAG Retriever...")
    
    try:
        # Mock corpus data
        corpus_texts = [
            "Netmera SDK provides push notification functionality for mobile apps",
            "iOS integration requires specific configuration in Xcode project",
            "Android setup involves Gradle configuration and API key setup",
            "User segmentation allows targeting specific user groups",
            "Campaign management enables automated marketing workflows"
        ]
        
        corpus_meta = [
            {"source": "netmera_docs", "url": "https://docs.netmera.com/sdk"},
            {"source": "netmera_docs", "url": "https://docs.netmera.com/ios"},
            {"source": "netmera_docs", "url": "https://docs.netmera.com/android"},
            {"source": "netmera_docs", "url": "https://docs.netmera.com/segmentation"},
            {"source": "netmera_docs", "url": "https://docs.netmera.com/campaigns"}
        ]
        
        # Test hybrid retriever
        from src.retrievers.hybrid_graphrag import HybridGraphRAGRetriever
        
        print("   Initializing hybrid retriever...")
        hybrid_retriever = HybridGraphRAGRetriever(corpus_texts, corpus_meta)
        
        # Test queries
        test_queries = [
            "How to setup Netmera SDK?",  # Should route to graph (setup workflow)
            "What is push notification?",  # Should route to vector (definition)
            "iOS Android integration together"  # Should route to hybrid
        ]
        
        for query in test_queries:
            print(f"\n   Testing query: '{query}'")
            context = hybrid_retriever.retrieve(query, k=3)
            
            print(f"   Route: {context.routing_info.get('route_type', 'unknown')}")
            print(f"   Vector docs: {len(context.vector_context)}")
            print(f"   Graph context: {'Yes' if context.graph_context else 'No'}")
            print(f"   Confidence: {context.combined_confidence:.2f}")
        
        print("✅ Hybrid retriever working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing hybrid retriever: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_langraph_integration():
    """Test LangGraph integration"""
    print("\n🔄 Testing LangGraph Integration...")
    
    try:
        # Mock corpus for testing
        corpus_texts = ["Netmera SDK installation guide", "Push notification setup"]
        corpus_meta = [{"source": "test", "url": "test.com"}] * 2
        
        from src.graph.app_graph import build_app_graph
        
        # Test with GraphRAG enabled
        print("   Building graph with GraphRAG enabled...")
        graph = build_app_graph(corpus_texts, corpus_meta, use_graphrag=True)
        
        # Test a simple query
        print("   Testing query execution...")
        result = graph.invoke({"query": "Netmera SDK nedir?"})
        
        print(f"   Answer generated: {len(result.get('answer', ''))>0}")
        print(f"   Graph context: {'graph_context' in result}")
        print(f"   Routing info: {'routing_info' in result}")
        
        print("✅ LangGraph integration working!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing LangGraph integration: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 GraphRAG Integration Test")
    print("=" * 50)
    
    # Set up environment
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'test-key')
    
    success = True
    
    # Run tests
    success &= test_graphrag_components()
    success &= test_hybrid_retriever()
    success &= test_langraph_integration()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! GraphRAG integration is ready.")
    else:
        print("❌ Some tests failed. Check the errors above.")
    
    print("\nNext steps:")
    print("1. Install missing dependencies: pip install -r requirements.txt")
    print("2. Set up OpenAI API key in environment")
    print("3. Run the Streamlit app: streamlit run app.py")
    print("4. Toggle GraphRAG in the sidebar and test different query types")

