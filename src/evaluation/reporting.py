"""
LangSmith Evaluation Reporting and Analysis Utilities
Evaluation sonuçlarını analiz etmek ve raporlamak için araçlar
"""

import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from langsmith import Client
from langsmith.schemas import Run

from .config import EVALUATOR_CONFIGS, PERFORMANCE_BENCHMARKS, get_evaluation_config


@dataclass
class EvaluationSummary:
    """Evaluation özet bilgileri"""
    experiment_name: str
    dataset_name: str
    total_examples: int
    completion_rate: float
    average_scores: Dict[str, float]
    benchmark_comparison: Dict[str, str]  # excellent/good/acceptable
    execution_time: float
    timestamp: datetime


class EvaluationReporter:
    """LangSmith evaluation sonuçlarını analiz ve raporlama sınıfı"""
    
    def __init__(self, langsmith_client: Optional[Client] = None):
        """
        Initialize reporter
        
        Args:
            langsmith_client: LangSmith client (None ise otomatik oluşturulur)
        """
        self.client = langsmith_client or Client()
        self.config = get_evaluation_config()
        self.reports_dir = Path(self.config["report"]["export_path"])
        self.reports_dir.mkdir(exist_ok=True)
        
        # Visualization settings
        plt.style.use('default')
        sns.set_palette("husl")
    
    def get_experiment_runs(self, experiment_name: str) -> List[Run]:
        """Experiment'taki tüm run'ları getir"""
        try:
            runs = list(self.client.list_runs(
                project_name=self.config["langsmith"]["project"],
                experiment_name=experiment_name
            ))
            return runs
        except Exception as e:
            print(f"Error fetching runs for experiment {experiment_name}: {e}")
            return []
    
    def get_recent_experiments(self, days: int = 7) -> List[str]:
        """Son N gündeki experiment'leri getir"""
        try:
            since = datetime.now() - timedelta(days=days)
            experiments = []
            
            # Get runs from the project
            runs = list(self.client.list_runs(
                project_name=self.config["langsmith"]["project"],
                start_time=since
            ))
            
            # Extract unique experiment names
            experiment_names = set()
            for run in runs:
                if hasattr(run, 'extra') and run.extra and 'experiment_name' in run.extra:
                    experiment_names.add(run.extra['experiment_name'])
            
            return list(experiment_names)
            
        except Exception as e:
            print(f"Error fetching recent experiments: {e}")
            return []
    
    def analyze_experiment(self, experiment_name: str) -> EvaluationSummary:
        """Tek bir experiment'ı analiz et"""
        runs = self.get_experiment_runs(experiment_name)
        
        if not runs:
            raise ValueError(f"No runs found for experiment: {experiment_name}")
        
        # Evaluation run'larını filtrele (evaluation feedback'li olanlar)
        eval_runs = []
        for run in runs:
            if hasattr(run, 'feedback_stats') and run.feedback_stats:
                eval_runs.append(run)
        
        if not eval_runs:
            # Fallback: tüm run'ları kullan
            eval_runs = runs
        
        # Skorları topla
        all_scores = {}
        for evaluator in EVALUATOR_CONFIGS.keys():
            all_scores[evaluator] = []
        
        total_examples = len(eval_runs)
        successful_runs = 0
        total_execution_time = 0
        
        for run in eval_runs:
            if run.status == "success":
                successful_runs += 1
            
            if run.total_time:
                total_execution_time += run.total_time / 1000  # ms to seconds
            
            # Feedback'lerden skorları çıkar
            if hasattr(run, 'feedback_stats') and run.feedback_stats:
                for feedback in run.feedback_stats:
                    evaluator_key = feedback.key
                    if evaluator_key in all_scores:
                        all_scores[evaluator_key].append(feedback.score or 0.0)
        
        # Ortalama skorları hesapla
        average_scores = {}
        for evaluator, scores in all_scores.items():
            if scores:
                average_scores[evaluator] = sum(scores) / len(scores)
            else:
                average_scores[evaluator] = 0.0
        
        # Benchmark karşılaştırması
        benchmark_comparison = {}
        for evaluator, avg_score in average_scores.items():
            if evaluator in PERFORMANCE_BENCHMARKS:
                benchmarks = PERFORMANCE_BENCHMARKS[evaluator]
                if avg_score >= benchmarks["excellent"]:
                    benchmark_comparison[evaluator] = "excellent"
                elif avg_score >= benchmarks["good"]:
                    benchmark_comparison[evaluator] = "good"
                elif avg_score >= benchmarks["acceptable"]:
                    benchmark_comparison[evaluator] = "acceptable"
                else:
                    benchmark_comparison[evaluator] = "poor"
        
        # Dataset adını tahmin et (experiment name'den)
        dataset_name = "unknown"
        for dataset in self.config["datasets"].keys():
            if dataset in experiment_name.lower():
                dataset_name = dataset
                break
        
        return EvaluationSummary(
            experiment_name=experiment_name,
            dataset_name=dataset_name,
            total_examples=total_examples,
            completion_rate=successful_runs / total_examples if total_examples > 0 else 0,
            average_scores=average_scores,
            benchmark_comparison=benchmark_comparison,
            execution_time=total_execution_time,
            timestamp=datetime.now()
        )
    
    def generate_score_chart(self, summaries: List[EvaluationSummary], 
                           output_path: Optional[Path] = None) -> Path:
        """Skorları gösteren bar chart oluştur"""
        if not summaries:
            raise ValueError("No summaries provided for chart generation")
        
        # Data preparation
        data = []
        for summary in summaries:
            for evaluator, score in summary.average_scores.items():
                data.append({
                    'Experiment': summary.experiment_name,
                    'Evaluator': EVALUATOR_CONFIGS.get(evaluator, {}).get('name', evaluator),
                    'Score': score,
                    'Benchmark': summary.benchmark_comparison.get(evaluator, 'unknown')
                })
        
        df = pd.DataFrame(data)
        
        # Create chart
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Grouped bar chart
        sns.barplot(data=df, x='Evaluator', y='Score', hue='Experiment', ax=ax)
        
        # Benchmark lines
        evaluators = df['Evaluator'].unique()
        for i, evaluator_display in enumerate(evaluators):
            # Find original evaluator key
            evaluator_key = None
            for key, config in EVALUATOR_CONFIGS.items():
                if config.get('name') == evaluator_display:
                    evaluator_key = key
                    break
            
            if evaluator_key and evaluator_key in PERFORMANCE_BENCHMARKS:
                benchmarks = PERFORMANCE_BENCHMARKS[evaluator_key]
                ax.axhline(y=benchmarks["excellent"], color='green', linestyle='--', alpha=0.5)
                ax.axhline(y=benchmarks["good"], color='orange', linestyle='--', alpha=0.5)
                ax.axhline(y=benchmarks["acceptable"], color='red', linestyle='--', alpha=0.5)
        
        ax.set_title('Evaluation Scores by Evaluator', fontsize=16, fontweight='bold')
        ax.set_ylabel('Score', fontsize=12)
        ax.set_xlabel('Evaluator', fontsize=12)
        ax.legend(title='Experiment', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save chart
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"evaluation_scores_{timestamp}.png"
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_comparison_chart(self, summaries: List[EvaluationSummary],
                                output_path: Optional[Path] = None) -> Path:
        """Dataset'ler arası karşılaştırma grafiği"""
        if not summaries:
            raise ValueError("No summaries provided for comparison chart")
        
        # Group by dataset
        dataset_scores = {}
        for summary in summaries:
            dataset = summary.dataset_name
            if dataset not in dataset_scores:
                dataset_scores[dataset] = {}
            
            for evaluator, score in summary.average_scores.items():
                if evaluator not in dataset_scores[dataset]:
                    dataset_scores[dataset][evaluator] = []
                dataset_scores[dataset][evaluator].append(score)
        
        # Calculate averages per dataset
        dataset_averages = {}
        for dataset, evaluators in dataset_scores.items():
            dataset_averages[dataset] = {}
            for evaluator, scores in evaluators.items():
                dataset_averages[dataset][evaluator] = sum(scores) / len(scores)
        
        # Create radar chart
        fig, axes = plt.subplots(1, len(dataset_averages), figsize=(5*len(dataset_averages), 5))
        if len(dataset_averages) == 1:
            axes = [axes]
        
        evaluator_names = list(EVALUATOR_CONFIGS.keys())
        
        for i, (dataset, scores) in enumerate(dataset_averages.items()):
            ax = axes[i]
            
            # Prepare data for radar chart
            values = [scores.get(evaluator, 0) for evaluator in evaluator_names]
            values += [values[0]]  # Close the polygon
            
            labels = [EVALUATOR_CONFIGS[eval].get('name', eval) for eval in evaluator_names]
            labels += [labels[0]]
            
            # Create radar chart
            angles = [n / len(evaluator_names) * 2 * 3.14159 for n in range(len(evaluator_names))]
            angles += [angles[0]]
            
            ax = plt.subplot(1, len(dataset_averages), i+1, projection='polar')
            ax.plot(angles, values, 'o-', linewidth=2, label=dataset)
            ax.fill(angles, values, alpha=0.25)
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels[:-1])
            ax.set_ylim(0, 1)
            ax.set_title(f'Dataset: {dataset}', y=1.08)
            ax.grid(True)
        
        plt.suptitle('Performance Comparison by Dataset', fontsize=16, fontweight='bold')
        plt.tight_layout()
        
        # Save chart
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"dataset_comparison_{timestamp}.png"
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        return output_path
    
    def generate_html_report(self, summaries: List[EvaluationSummary],
                           output_path: Optional[Path] = None) -> Path:
        """Comprehensive HTML report oluştur"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"evaluation_report_{timestamp}.html"
        
        # Generate charts
        score_chart = self.generate_score_chart(summaries)
        comparison_chart = self.generate_comparison_chart(summaries)
        
        # HTML template
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Netmera Chatbot Evaluation Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #f0f8ff; padding: 20px; border-radius: 5px; }}
                .summary {{ margin: 20px 0; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; }}
                .excellent {{ background-color: #d4edda; }}
                .good {{ background-color: #fff3cd; }}
                .acceptable {{ background-color: #f8d7da; }}
                .poor {{ background-color: #f5c6cb; }}
                .chart {{ text-align: center; margin: 20px 0; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Netmera Chatbot Evaluation Report</h1>
                <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Total Experiments: {len(summaries)}</p>
            </div>
        """
        
        # Summary statistics
        html_content += "<h2>📊 Summary Statistics</h2>"
        
        total_examples = sum(s.total_examples for s in summaries)
        avg_completion = sum(s.completion_rate for s in summaries) / len(summaries) if summaries else 0
        total_time = sum(s.execution_time for s in summaries)
        
        html_content += f"""
        <div class="summary">
            <div class="metric">
                <h3>Total Examples</h3>
                <p>{total_examples}</p>
            </div>
            <div class="metric">
                <h3>Average Completion Rate</h3>
                <p>{avg_completion:.1%}</p>
            </div>
            <div class="metric">
                <h3>Total Execution Time</h3>
                <p>{total_time:.1f} seconds</p>
            </div>
        </div>
        """
        
        # Charts
        html_content += f"""
        <h2>📈 Performance Charts</h2>
        <div class="chart">
            <h3>Evaluation Scores</h3>
            <img src="{score_chart.name}" alt="Evaluation Scores" style="max-width: 100%;">
        </div>
        <div class="chart">
            <h3>Dataset Comparison</h3>
            <img src="{comparison_chart.name}" alt="Dataset Comparison" style="max-width: 100%;">
        </div>
        """
        
        # Detailed results table
        html_content += "<h2>📋 Detailed Results</h2>"
        html_content += "<table>"
        html_content += "<tr><th>Experiment</th><th>Dataset</th><th>Examples</th><th>Completion Rate</th>"
        
        for evaluator_key, config in EVALUATOR_CONFIGS.items():
            html_content += f"<th>{config['name']}</th>"
        
        html_content += "</tr>"
        
        for summary in summaries:
            html_content += f"""
            <tr>
                <td>{summary.experiment_name}</td>
                <td>{summary.dataset_name}</td>
                <td>{summary.total_examples}</td>
                <td>{summary.completion_rate:.1%}</td>
            """
            
            for evaluator_key in EVALUATOR_CONFIGS.keys():
                score = summary.average_scores.get(evaluator_key, 0)
                benchmark = summary.benchmark_comparison.get(evaluator_key, 'unknown')
                html_content += f'<td class="{benchmark}">{score:.3f}</td>'
            
            html_content += "</tr>"
        
        html_content += "</table>"
        
        # Recommendations
        html_content += "<h2>💡 Recommendations</h2>"
        html_content += "<ul>"
        
        # Analyze overall performance
        avg_scores = {}
        for evaluator in EVALUATOR_CONFIGS.keys():
            scores = [s.average_scores.get(evaluator, 0) for s in summaries]
            avg_scores[evaluator] = sum(scores) / len(scores) if scores else 0
        
        # Generate recommendations based on lowest scores
        lowest_scores = sorted(avg_scores.items(), key=lambda x: x[1])
        
        for evaluator, score in lowest_scores[:2]:  # Top 2 improvement areas
            config = EVALUATOR_CONFIGS[evaluator]
            if score < config["threshold"]:
                html_content += f"<li>Improve <strong>{config['name']}</strong> (current: {score:.3f}, target: {config['threshold']:.3f})</li>"
        
        html_content += "</ul>"
        
        html_content += """
        </body>
        </html>
        """
        
        # Write HTML file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return output_path
    
    def export_to_csv(self, summaries: List[EvaluationSummary],
                     output_path: Optional[Path] = None) -> Path:
        """CSV formatında export et"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.reports_dir / f"evaluation_results_{timestamp}.csv"
        
        # Prepare data
        data = []
        for summary in summaries:
            row = {
                'experiment_name': summary.experiment_name,
                'dataset_name': summary.dataset_name,
                'total_examples': summary.total_examples,
                'completion_rate': summary.completion_rate,
                'execution_time': summary.execution_time,
                'timestamp': summary.timestamp.isoformat()
            }
            
            # Add evaluator scores
            for evaluator, score in summary.average_scores.items():
                row[f'{evaluator}_score'] = score
                row[f'{evaluator}_benchmark'] = summary.benchmark_comparison.get(evaluator, 'unknown')
            
            data.append(row)
        
        # Create DataFrame and save
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
        
        return output_path
    
    def generate_comprehensive_report(self, experiment_names: List[str],
                                    report_name: Optional[str] = None) -> Dict[str, Path]:
        """Kapsamlı rapor oluştur (tüm formatlar)"""
        if not report_name:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"evaluation_report_{timestamp}"
        
        # Analyze all experiments
        summaries = []
        for exp_name in experiment_names:
            try:
                summary = self.analyze_experiment(exp_name)
                summaries.append(summary)
            except Exception as e:
                print(f"Warning: Could not analyze experiment {exp_name}: {e}")
        
        if not summaries:
            raise ValueError("No valid experiment summaries could be generated")
        
        # Generate all report formats
        reports = {}
        
        # HTML Report
        html_path = self.reports_dir / f"{report_name}.html"
        reports['html'] = self.generate_html_report(summaries, html_path)
        
        # CSV Export
        csv_path = self.reports_dir / f"{report_name}.csv"
        reports['csv'] = self.export_to_csv(summaries, csv_path)
        
        # JSON Export
        json_path = self.reports_dir / f"{report_name}.json"
        json_data = [
            {
                'experiment_name': s.experiment_name,
                'dataset_name': s.dataset_name,
                'total_examples': s.total_examples,
                'completion_rate': s.completion_rate,
                'average_scores': s.average_scores,
                'benchmark_comparison': s.benchmark_comparison,
                'execution_time': s.execution_time,
                'timestamp': s.timestamp.isoformat()
            }
            for s in summaries
        ]
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        reports['json'] = json_path
        
        print(f"📊 Comprehensive report generated:")
        for format_type, path in reports.items():
            print(f"   {format_type.upper()}: {path}")
        
        return reports


def main():
    """Reporting tool main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Netmera Chatbot Evaluation Reporting Tool")
    parser.add_argument("--experiments", nargs="+", help="Experiment names to analyze")
    parser.add_argument("--recent", type=int, default=7, help="Analyze experiments from last N days")
    parser.add_argument("--output", help="Output file prefix")
    
    args = parser.parse_args()
    
    try:
        reporter = EvaluationReporter()
        
        if args.experiments:
            experiment_names = args.experiments
        else:
            print(f"Fetching experiments from last {args.recent} days...")
            experiment_names = reporter.get_recent_experiments(args.recent)
            
            if not experiment_names:
                print("No recent experiments found")
                return
        
        print(f"Generating reports for {len(experiment_names)} experiments...")
        reports = reporter.generate_comprehensive_report(experiment_names, args.output)
        
        print("✅ Report generation completed!")
        
    except Exception as e:
        print(f"❌ Error generating reports: {e}")


if __name__ == "__main__":
    main()
