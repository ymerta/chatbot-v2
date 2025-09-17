#!/usr/bin/env python3
"""
Test query expansion functionality
"""

from src.graphrag.query_expansion import QueryExpander

def test_query_expansion():
    """Test query expansion with various Netmera-specific queries"""
    print("🔍 Query Expansion Test")
    print("=" * 50)
    
    expander = QueryExpander()
    
    test_queries = [
        "segment kullanıcı",        # Should expand with "audience", "user group"
        "kampanya gönder",          # Should expand with "campaign", "messaging"
        "iOS kurulum",              # Should expand with "setup", "installation"
        "hata alıyorum",            # Should expand with "error", "problem"
        "push bildirim",            # Should expand with "notification", "alert"
        "webpush nasıl",            # Should expand with "web push", "browser notification"
        "API token",                # Should expand with "authentication", "api key"
        "Android gradle",           # Should expand with "build system", "dependency"
        "çok dilli kampanya",       # Should expand with "multi-language", "multilingual"
        "buton seti"                # Should expand with "button set", "action buttons"
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"{i}. Original: '{query}'")
        
        expanded = expander.expand_query(query)
        
        print(f"   Language: {expanded.language}")
        print(f"   Detected Entities: {expanded.detected_entities}")
        print(f"   Added Terms: {expanded.added_terms[:5]}")  # Show first 5
        print(f"   Expansion Confidence: {expanded.expansion_confidence:.2f}")
        print(f"   Expanded Query: '{expanded.expanded_query[:100]}...'")
        
        # Test cross-language variants
        variants = expander.create_cross_language_variants(query)
        if len(variants) > 1:
            print(f"   Cross-lang variant: '{variants[1][:80]}...'")
        
        print("-" * 50)
    
    # Test expansion decision logic
    print("\n📊 Expansion Decision Logic Test")
    print("=" * 50)
    
    test_scenarios = [
        (0, 0.1, "No results, low confidence"),
        (2, 0.3, "Few results, low confidence"), 
        (1, 0.6, "Very few results, good confidence"),
        (5, 0.8, "Good results, high confidence")
    ]
    
    for results_count, confidence, description in test_scenarios:
        should_expand = expander.should_expand_query(results_count, confidence)
        expand_text = "✅ EXPAND" if should_expand else "❌ NO EXPAND"
        print(f"{description}: {expand_text} (results: {results_count}, conf: {confidence})")
    
    # Test taxonomy stats
    print("\n📈 Taxonomy Statistics")
    print("=" * 50)
    stats = expander.get_stats()
    for key, value in stats.items():
        print(f"{key}: {value}")
    
    print("\n✅ Query expansion test completed!")

if __name__ == "__main__":
    test_query_expansion()
