#!/usr/bin/env python3
"""Test comparison query routing"""

from src.graphrag.query_router import QueryRouter

def test_comparison_routing():
    router = QueryRouter()

    test_queries = [
        'iOS ve Android Netmera entegrasyonu arasındaki farklar nelerdir?',
        'Push notification iOS vs Android farkı',
        'iOS Android karşılaştır', 
        'Netmera SDK differences between platforms',
        'CocoaPods vs Gradle comparison',
        'Swift ile Kotlin arasındaki fark'
    ]

    print('🔍 Comparison Query Routing Test')
    print('=' * 50)

    for query in test_queries:
        result = router.route_query(query)
        print(f'Query: "{query}"')
        print(f'Route: {result["route_type"].value} / {result["strategy"].value}')
        print(f'Scores: Graph={result["graph_score"]:.2f}, Vector={result["vector_score"]:.2f}')
        print(f'Reasoning: {result["reasoning"]}')
        print('-' * 50)

if __name__ == "__main__":
    test_comparison_routing()
