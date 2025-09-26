"""
Chunking Strategy Evaluator
Comprehensive evaluation framework for different chunking approaches
"""

import json
import time
import numpy as np
from typing import List, Dict, Tuple, Any
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
import os

# Optional imports for visualization
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    import pandas as pd
    HAS_PLOTTING = True
except ImportError:
    HAS_PLOTTING = False
    print("⚠️  Visualization packages not available. Charts will be skipped.")

# Optional imports for scikit-learn
try:
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False
    print("⚠️  scikit-learn not available. Semantic coherence evaluation will be skipped.")

class ChunkingEvaluator:
    """Evaluate and compare different chunking strategies"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
        self.evaluation_metrics = {}
        
    def evaluate_chunking_strategy(self, chunks: List[Dict], 
                                 strategy_name: str,
                                 test_queries: List[str] = None) -> Dict:
        """
        Comprehensive evaluation of a chunking strategy
        
        Args:
            chunks: List of chunks from the strategy
            strategy_name: Name identifier for the strategy
            test_queries: Optional test queries for retrieval evaluation
            
        Returns:
            Dictionary with evaluation metrics
        """
        print(f"📊 Evaluating chunking strategy: {strategy_name}")
        
        # Basic statistics
        chunk_sizes = [len(chunk["text"]) for chunk in chunks]
        
        basic_metrics = {
            "total_chunks": len(chunks),
            "avg_chunk_size": np.mean(chunk_sizes),
            "std_chunk_size": np.std(chunk_sizes),
            "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
            "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
            "median_chunk_size": np.median(chunk_sizes),
            "size_consistency": 1 - (np.std(chunk_sizes) / np.mean(chunk_sizes)) if np.mean(chunk_sizes) > 0 else 0
        }
        
        # Content quality metrics
        content_metrics = self._evaluate_content_quality(chunks)
        
        # Semantic coherence metrics
        coherence_metrics = self._evaluate_semantic_coherence(chunks)
        
        # Enhancement metrics (if enhanced chunks)
        enhancement_metrics = self._evaluate_enhancements(chunks)
        
        # Retrieval performance (if test queries provided)
        retrieval_metrics = {}
        if test_queries:
            retrieval_metrics = self._evaluate_retrieval_performance(chunks, test_queries, strategy_name)
        
        # Combine all metrics
        evaluation_result = {
            "strategy_name": strategy_name,
            "timestamp": time.time(),
            "basic_metrics": basic_metrics,
            "content_metrics": content_metrics,
            "coherence_metrics": coherence_metrics,
            "enhancement_metrics": enhancement_metrics,
            "retrieval_metrics": retrieval_metrics,
            "overall_score": self._calculate_overall_score(
                basic_metrics, content_metrics, coherence_metrics, enhancement_metrics
            )
        }
        
        self.evaluation_metrics[strategy_name] = evaluation_result
        return evaluation_result
    
    def _evaluate_content_quality(self, chunks: List[Dict]) -> Dict:
        """Evaluate content quality aspects"""
        
        # Content type distribution
        content_types = {}
        has_code_count = 0
        has_steps_count = 0
        tech_terms_count = 0
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            
            # Content type distribution
            content_type = metadata.get("content_type", "unknown")
            content_types[content_type] = content_types.get(content_type, 0) + 1
            
            # Feature counts
            if metadata.get("has_code", False):
                has_code_count += 1
            if metadata.get("has_steps", False):
                has_steps_count += 1
            
            tech_terms = metadata.get("tech_terms", [])
            tech_terms_count += len(tech_terms)
        
        total_chunks = len(chunks)
        
        return {
            "content_type_distribution": content_types,
            "code_preservation_ratio": has_code_count / total_chunks if total_chunks > 0 else 0,
            "step_preservation_ratio": has_steps_count / total_chunks if total_chunks > 0 else 0,
            "avg_tech_terms_per_chunk": tech_terms_count / total_chunks if total_chunks > 0 else 0,
            "content_diversity_score": len(content_types) / 6  # Assuming 6 possible content types
        }
    
    def _evaluate_semantic_coherence(self, chunks: List[Dict]) -> Dict:
        """Evaluate semantic coherence using embeddings"""
        if not HAS_SKLEARN:
            return {"error": "scikit-learn not available for coherence evaluation"}
            
        if len(chunks) < 2:
            return {"error": "Not enough chunks for coherence evaluation"}
        
        try:
            print("🧮 Computing embeddings for coherence analysis...")
            
            # Sample chunks for embedding (to avoid API costs)
            sample_size = min(50, len(chunks))
            sample_chunks = chunks[:sample_size]
            
            # Get embeddings
            texts = [chunk["text"][:1000] for chunk in sample_chunks]  # Truncate for cost
            embeddings_matrix = self.embeddings.embed_documents(texts)
            
            # Calculate pairwise similarities
            similarities = cosine_similarity(embeddings_matrix)
            
            # Remove diagonal (self-similarity)
            np.fill_diagonal(similarities, np.nan)
            
            # Calculate metrics
            avg_similarity = np.nanmean(similarities)
            std_similarity = np.nanstd(similarities)
            
            # Adjacent chunk coherence (chunks that should be related)
            adjacent_similarities = []
            for i in range(len(sample_chunks) - 1):
                if not np.isnan(similarities[i][i + 1]):
                    adjacent_similarities.append(similarities[i][i + 1])
            
            avg_adjacent_similarity = np.mean(adjacent_similarities) if adjacent_similarities else 0
            
            return {
                "avg_similarity": float(avg_similarity),
                "std_similarity": float(std_similarity),
                "avg_adjacent_similarity": float(avg_adjacent_similarity),
                "coherence_score": float(avg_adjacent_similarity * 0.7 + avg_similarity * 0.3),
                "sample_size": sample_size
            }
            
        except Exception as e:
            print(f"⚠️ Coherence evaluation failed: {e}")
            return {"error": str(e)}
    
    def _evaluate_enhancements(self, chunks: List[Dict]) -> Dict:
        """Evaluate enhancement features like summaries"""
        
        enhanced_chunks = 0
        prev_summary_count = 0
        next_summary_count = 0
        enhancement_size_increase = []
        
        for chunk in chunks:
            metadata = chunk.get("metadata", {})
            enhancement_features = metadata.get("enhancement_features", {})
            
            if enhancement_features.get("is_enhanced", False):
                enhanced_chunks += 1
                
                if enhancement_features.get("has_prev_summary", False):
                    prev_summary_count += 1
                    
                if enhancement_features.get("has_next_summary", False):
                    next_summary_count += 1
                
                # Calculate size increase due to enhancements
                original_text = chunk.get("original_text", "")
                enhanced_text = chunk.get("text", "")
                if original_text and enhanced_text:
                    size_increase = (len(enhanced_text) - len(original_text)) / len(original_text)
                    enhancement_size_increase.append(size_increase)
        
        total_chunks = len(chunks)
        
        return {
            "enhancement_ratio": enhanced_chunks / total_chunks if total_chunks > 0 else 0,
            "prev_summary_ratio": prev_summary_count / total_chunks if total_chunks > 0 else 0,
            "next_summary_ratio": next_summary_count / total_chunks if total_chunks > 0 else 0,
            "avg_size_increase": np.mean(enhancement_size_increase) if enhancement_size_increase else 0,
            "enhancement_effectiveness": (prev_summary_count + next_summary_count) / (2 * total_chunks) if total_chunks > 0 else 0
        }
    
    def _evaluate_retrieval_performance(self, chunks: List[Dict], 
                                      test_queries: List[str], 
                                      strategy_name: str) -> Dict:
        """Evaluate retrieval performance with test queries"""
        try:
            print(f"🔍 Evaluating retrieval performance for {strategy_name}...")
            
            # Create temporary FAISS index
            texts = [chunk["text"] for chunk in chunks]
            metadatas = [chunk.get("metadata", {}) for chunk in chunks]
            
            vectorstore = FAISS.from_texts(texts, self.embeddings, metadatas=metadatas)
            
            retrieval_scores = []
            relevance_scores = []
            
            for query in test_queries:
                # Retrieve top 5 chunks
                results = vectorstore.similarity_search_with_score(query, k=5)
                
                if results:
                    # Calculate average retrieval score (distance)
                    avg_distance = np.mean([score for _, score in results])
                    retrieval_scores.append(1 / (1 + avg_distance))  # Convert to similarity
                    
                    # Simple relevance check (contains query terms)
                    query_terms = query.lower().split()
                    relevance_count = 0
                    for doc, _ in results:
                        doc_text = doc.page_content.lower()
                        if any(term in doc_text for term in query_terms):
                            relevance_count += 1
                    
                    relevance_scores.append(relevance_count / len(results))
            
            return {
                "avg_retrieval_score": np.mean(retrieval_scores) if retrieval_scores else 0,
                "avg_relevance_score": np.mean(relevance_scores) if relevance_scores else 0,
                "queries_tested": len(test_queries),
                "retrieval_consistency": 1 - np.std(retrieval_scores) if len(retrieval_scores) > 1 else 1
            }
            
        except Exception as e:
            print(f"⚠️ Retrieval evaluation failed: {e}")
            return {"error": str(e)}
    
    def _calculate_overall_score(self, basic_metrics: Dict, content_metrics: Dict, 
                               coherence_metrics: Dict, enhancement_metrics: Dict) -> float:
        """Calculate overall quality score (0-1)"""
        
        score = 0.0
        weight_sum = 0.0
        
        # Size consistency (0.2 weight)
        size_consistency = basic_metrics.get("size_consistency", 0)
        score += size_consistency * 0.2
        weight_sum += 0.2
        
        # Content diversity (0.15 weight)
        content_diversity = content_metrics.get("content_diversity_score", 0)
        score += content_diversity * 0.15
        weight_sum += 0.15
        
        # Technical content preservation (0.2 weight)
        code_preservation = content_metrics.get("code_preservation_ratio", 0)
        step_preservation = content_metrics.get("step_preservation_ratio", 0)
        tech_preservation = (code_preservation + step_preservation) / 2
        score += tech_preservation * 0.2
        weight_sum += 0.2
        
        # Semantic coherence (0.25 weight)
        if "coherence_score" in coherence_metrics:
            coherence_score = coherence_metrics["coherence_score"]
            score += coherence_score * 0.25
            weight_sum += 0.25
        
        # Enhancement effectiveness (0.2 weight)
        enhancement_effectiveness = enhancement_metrics.get("enhancement_effectiveness", 0)
        score += enhancement_effectiveness * 0.2
        weight_sum += 0.2
        
        return score / weight_sum if weight_sum > 0 else 0
    
    def compare_strategies(self, strategies_results: Dict[str, Dict]) -> Dict:
        """Compare multiple chunking strategies"""
        
        comparison = {
            "strategies_compared": list(strategies_results.keys()),
            "best_strategy": "",
            "comparison_metrics": {},
            "recommendations": []
        }
        
        # Find best strategy by overall score
        best_score = 0
        best_strategy = ""
        
        for strategy_name, results in strategies_results.items():
            overall_score = results.get("overall_score", 0)
            if overall_score > best_score:
                best_score = overall_score
                best_strategy = strategy_name
        
        comparison["best_strategy"] = best_strategy
        comparison["best_score"] = best_score
        
        # Create comparison metrics
        metrics_to_compare = [
            "basic_metrics.avg_chunk_size",
            "basic_metrics.size_consistency", 
            "content_metrics.content_diversity_score",
            "coherence_metrics.coherence_score",
            "enhancement_metrics.enhancement_effectiveness",
            "overall_score"
        ]
        
        for metric in metrics_to_compare:
            metric_values = {}
            for strategy_name, results in strategies_results.items():
                try:
                    # Navigate nested dict path
                    value = results
                    for key in metric.split('.'):
                        value = value[key]
                    metric_values[strategy_name] = value
                except (KeyError, TypeError):
                    metric_values[strategy_name] = 0
            
            comparison["comparison_metrics"][metric] = metric_values
        
        # Generate recommendations
        comparison["recommendations"] = self._generate_recommendations(strategies_results)
        
        return comparison
    
    def _generate_recommendations(self, strategies_results: Dict[str, Dict]) -> List[str]:
        """Generate actionable recommendations based on evaluation results"""
        recommendations = []
        
        # Find strategy with best coherence
        best_coherence = 0
        best_coherence_strategy = ""
        
        for strategy_name, results in strategies_results.items():
            coherence_score = results.get("coherence_metrics", {}).get("coherence_score", 0)
            if coherence_score > best_coherence:
                best_coherence = coherence_score
                best_coherence_strategy = strategy_name
        
        if best_coherence_strategy:
            recommendations.append(
                f"✅ Use '{best_coherence_strategy}' for best semantic coherence (score: {best_coherence:.3f})"
            )
        
        # Check for enhancement effectiveness
        for strategy_name, results in strategies_results.items():
            enhancement_ratio = results.get("enhancement_metrics", {}).get("enhancement_ratio", 0)
            if enhancement_ratio > 0.8:
                recommendations.append(
                    f"🔄 '{strategy_name}' shows excellent enhancement coverage ({enhancement_ratio:.1%})"
                )
        
        # Size consistency recommendations
        for strategy_name, results in strategies_results.items():
            size_consistency = results.get("basic_metrics", {}).get("size_consistency", 0)
            if size_consistency < 0.5:
                recommendations.append(
                    f"⚠️ '{strategy_name}' has inconsistent chunk sizes - consider adjustment"
                )
        
        # Content preservation recommendations
        for strategy_name, results in strategies_results.items():
            code_preservation = results.get("content_metrics", {}).get("code_preservation_ratio", 0)
            if code_preservation > 0.3:
                recommendations.append(
                    f"💻 '{strategy_name}' excels at code preservation ({code_preservation:.1%})"
                )
        
        return recommendations
    
    def save_evaluation_report(self, output_file: str = "data/analysis/chunking_evaluation_report.json"):
        """Save comprehensive evaluation report"""
        
        report = {
            "evaluation_timestamp": time.time(),
            "strategies_evaluated": list(self.evaluation_metrics.keys()),
            "individual_results": self.evaluation_metrics,
            "comparison": self.compare_strategies(self.evaluation_metrics) if len(self.evaluation_metrics) > 1 else {},
            "summary": {
                "total_strategies": len(self.evaluation_metrics),
                "best_overall_strategy": "",
                "avg_overall_score": 0
            }
        }
        
        # Calculate summary stats
        if self.evaluation_metrics:
            scores = [results["overall_score"] for results in self.evaluation_metrics.values()]
            report["summary"]["avg_overall_score"] = np.mean(scores)
            
            best_strategy = max(self.evaluation_metrics.items(), 
                              key=lambda x: x[1]["overall_score"])
            report["summary"]["best_overall_strategy"] = best_strategy[0]
        
        # Save report (convert numpy types to Python types for JSON serialization)
        def convert_numpy_types(obj):
            if isinstance(obj, np.floating):
                return float(obj)
            elif isinstance(obj, np.integer):
                return int(obj)
            elif isinstance(obj, np.ndarray):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {key: convert_numpy_types(value) for key, value in obj.items()}
            elif isinstance(obj, list):
                return [convert_numpy_types(item) for item in obj]
            return obj
        
        report = convert_numpy_types(report)
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Evaluation report saved to {output_file}")
        return report
    
    def create_visualization(self, output_dir: str = "data/analysis/charts/"):
        """Create visualization charts for evaluation results"""
        
        if not HAS_PLOTTING:
            print("⚠️  Visualization packages not available. Skipping chart creation.")
            return
        
        if not self.evaluation_metrics:
            print("❌ No evaluation data to visualize")
            return
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Prepare data for plotting
        strategies = list(self.evaluation_metrics.keys())
        
        # Overall scores comparison
        overall_scores = [results["overall_score"] for results in self.evaluation_metrics.values()]
        
        plt.figure(figsize=(12, 8))
        
        # Subplot 1: Overall scores
        plt.subplot(2, 2, 1)
        bars = plt.bar(strategies, overall_scores, color='skyblue', alpha=0.7)
        plt.title('Overall Strategy Scores')
        plt.ylabel('Score (0-1)')
        plt.xticks(rotation=45)
        
        # Add value labels on bars
        for bar, score in zip(bars, overall_scores):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{score:.3f}', ha='center', va='bottom')
        
        # Subplot 2: Chunk size distribution
        plt.subplot(2, 2, 2)
        avg_sizes = [results["basic_metrics"]["avg_chunk_size"] for results in self.evaluation_metrics.values()]
        std_sizes = [results["basic_metrics"]["std_chunk_size"] for results in self.evaluation_metrics.values()]
        
        plt.errorbar(strategies, avg_sizes, yerr=std_sizes, fmt='o-', capsize=5, alpha=0.7)
        plt.title('Average Chunk Sizes')
        plt.ylabel('Characters')
        plt.xticks(rotation=45)
        
        # Subplot 3: Content metrics
        plt.subplot(2, 2, 3)
        content_diversity = [results["content_metrics"]["content_diversity_score"] for results in self.evaluation_metrics.values()]
        code_preservation = [results["content_metrics"]["code_preservation_ratio"] for results in self.evaluation_metrics.values()]
        
        x = np.arange(len(strategies))
        width = 0.35
        
        plt.bar(x - width/2, content_diversity, width, label='Content Diversity', alpha=0.7)
        plt.bar(x + width/2, code_preservation, width, label='Code Preservation', alpha=0.7)
        
        plt.title('Content Quality Metrics')
        plt.ylabel('Score (0-1)')
        plt.xticks(x, strategies, rotation=45)
        plt.legend()
        
        # Subplot 4: Enhancement effectiveness
        plt.subplot(2, 2, 4)
        enhancement_ratios = [results["enhancement_metrics"]["enhancement_effectiveness"] for results in self.evaluation_metrics.values()]
        
        plt.pie(enhancement_ratios, labels=strategies, autopct='%1.1f%%', startangle=90)
        plt.title('Enhancement Effectiveness')
        
        plt.tight_layout()
        plt.savefig(f"{output_dir}/chunking_strategies_comparison.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 Visualization saved to {output_dir}/chunking_strategies_comparison.png")


# Test queries for evaluation
DEFAULT_TEST_QUERIES = [
    "How to implement Netmera SDK in Android?",
    "iOS push notification setup",
    "API authentication methods", 
    "Campaign creation tutorial",
    "Analytics integration guide",
    "Android SDK initialization steps",
    "Troubleshooting push notifications",
    "User segmentation API",
    "Journey orchestration setup",
    "Error handling best practices"
]


def run_comprehensive_evaluation(chunking_strategies: Dict[str, List[Dict]], 
                               test_queries: List[str] = None,
                               save_report: bool = True) -> Dict:
    """
    Run comprehensive evaluation of multiple chunking strategies
    
    Args:
        chunking_strategies: Dict mapping strategy names to their chunk lists
        test_queries: Optional test queries for retrieval evaluation
        save_report: Whether to save the evaluation report
        
    Returns:
        Complete evaluation report
    """
    
    if test_queries is None:
        test_queries = DEFAULT_TEST_QUERIES
    
    evaluator = ChunkingEvaluator()
    
    print("🎯 Running comprehensive chunking evaluation...")
    print(f"📝 Strategies to evaluate: {list(chunking_strategies.keys())}")
    print(f"🔍 Test queries: {len(test_queries)}")
    print("=" * 60)
    
    # Evaluate each strategy
    for strategy_name, chunks in chunking_strategies.items():
        print(f"\n📊 Evaluating: {strategy_name}")
        print("-" * 40)
        
        results = evaluator.evaluate_chunking_strategy(
            chunks, 
            strategy_name, 
            test_queries
        )
        
        print(f"✅ Overall Score: {results['overall_score']:.3f}")
        print(f"📈 Total Chunks: {results['basic_metrics']['total_chunks']}")
        print(f"📏 Avg Chunk Size: {results['basic_metrics']['avg_chunk_size']:.0f} chars")
        
        if "coherence_score" in results["coherence_metrics"]:
            print(f"🧠 Coherence Score: {results['coherence_metrics']['coherence_score']:.3f}")
        
        if results["enhancement_metrics"]["enhancement_ratio"] > 0:
            print(f"🔄 Enhancement Ratio: {results['enhancement_metrics']['enhancement_ratio']:.1%}")
    
    # Generate comparison and recommendations
    print(f"\n🏆 Generating comparison and recommendations...")
    comparison = evaluator.compare_strategies(evaluator.evaluation_metrics)
    
    print(f"\n🥇 Best Strategy: {comparison['best_strategy']} (Score: {comparison['best_score']:.3f})")
    print("\n💡 Recommendations:")
    for rec in comparison['recommendations']:
        print(f"   {rec}")
    
    # Save report and create visualizations
    if save_report:
        report = evaluator.save_evaluation_report()
        evaluator.create_visualization()
        return report
    
    return {
        "individual_results": evaluator.evaluation_metrics,
        "comparison": comparison
    }


if __name__ == "__main__":
    print("📊 Chunking Strategy Evaluator")
    print("=" * 50)
    print("This module provides comprehensive evaluation of chunking strategies")
    print("Use run_comprehensive_evaluation() to compare multiple strategies")
