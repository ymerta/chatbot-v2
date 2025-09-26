"""
Enhanced Semantic Chunking with Overlapping Summaries
Implements advanced chunking strategies with context preservation
"""

import re
import os
from typing import List, Dict, Tuple, Optional
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import FAISS
import json
import time

class EnhancedSemanticChunker:
    """Enhanced chunking with overlapping summaries and adaptive sizing"""
    
    def __init__(self, 
                 chunk_size: int = 1200,
                 chunk_overlap: int = 200,
                 min_chunk_size: int = 100,
                 max_chunk_size: int = 2500,
                 add_summaries: bool = True,
                 summary_length: int = 150):
        """
        Initialize enhanced semantic chunker
        
        Args:
            chunk_size: Base chunk size for experimentation
            chunk_overlap: Traditional overlap between chunks
            min_chunk_size: Minimum viable chunk size
            max_chunk_size: Maximum chunk size before force splitting
            add_summaries: Whether to add previous/next chunk summaries
            summary_length: Target length for chunk summaries
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.add_summaries = add_summaries
        self.summary_length = summary_length
        
        # Initialize OpenAI for summary generation
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=200
        )
        
        # Smart separators prioritizing structure preservation
        self.separators = [
            "\n\n\n",      # Major section breaks
            "\n\n",        # Paragraph breaks
            "\n### ",      # H3 headers
            "\n## ",       # H2 headers
            "\n# ",        # H1 headers
            "\n- ",        # List items
            "\n1. ",       # Numbered lists
            ". ",          # Sentence endings
            "! ",          # Exclamations
            "? ",          # Questions
            "\n",          # Line breaks
            " ",           # Spaces
            ""             # Character level (last resort)
        ]
        
        # Experimental chunk size configurations
        self.size_experiments = {
            "small": {"base": 800, "overlap": 150},
            "medium": {"base": 1200, "overlap": 200}, 
            "large": {"base": 1600, "overlap": 250},
            "xlarge": {"base": 2000, "overlap": 300},
            "adaptive": {"base": 1200, "overlap": 200}  # Will be dynamically adjusted
        }

    def detect_content_type(self, text: str) -> str:
        """Enhanced content type detection"""
        text_lower = text.lower()
        
        # Code-heavy content (enhanced detection)
        code_indicators = [
            "```", "gradle", "implementation", "json", "xml", "swift", "kotlin",
            "import ", "package ", "class ", "function ", "def ", "var ", "let "
        ]
        if any(indicator in text_lower for indicator in code_indicators) or \
           re.search(r'\{[\s\S]*\}', text) or \
           re.search(r'[\w]+\([\w\s,]*\)', text):
            return "code"
        
        # API documentation (enhanced)
        api_indicators = ["api", "endpoint", "http", "rest", "post", "get", "put", "delete", "curl"]
        if any(indicator in text_lower for indicator in api_indicators):
            return "api"
        
        # Configuration/Setup guides
        setup_indicators = ["setup", "install", "configure", "kurulum", "yapılandırma", "ayarlama"]
        if any(indicator in text_lower for indicator in setup_indicators):
            return "setup"
        
        # Step-by-step guides (enhanced)
        if (re.search(r'\n\d+\.', text) or
            "adım" in text_lower or
            "step" in text_lower or
            "first" in text_lower or
            "then" in text_lower):
            return "tutorial"
        
        # Troubleshooting content
        troubleshoot_indicators = ["error", "problem", "issue", "fix", "solve", "hata", "sorun", "çözüm"]
        if any(indicator in text_lower for indicator in troubleshoot_indicators):
            return "troubleshooting"
        
        return "general"

    def get_adaptive_chunk_size(self, content_type: str, text_length: int) -> Tuple[int, int]:
        """Get adaptive chunk size based on content type and text length"""
        base_size = self.chunk_size
        base_overlap = self.chunk_overlap
        
        # Content type multipliers
        multipliers = {
            "code": 1.6,           # Larger chunks for code context
            "api": 1.3,            # Medium-large for API docs
            "setup": 1.4,          # Larger for setup procedures
            "tutorial": 1.5,       # Large for step preservation
            "troubleshooting": 1.2, # Slightly larger for problem context
            "general": 1.0         # Standard size
        }
        
        multiplier = multipliers.get(content_type, 1.0)
        
        # Adaptive sizing based on text length
        if text_length < 500:
            # Very short text - use smaller chunks
            size_adjustment = 0.7
        elif text_length < 1500:
            # Short text - use medium chunks
            size_adjustment = 0.9
        elif text_length > 5000:
            # Long text - use larger chunks
            size_adjustment = 1.2
        else:
            # Standard text length
            size_adjustment = 1.0
        
        final_size = int(base_size * multiplier * size_adjustment)
        final_overlap = int(base_overlap * multiplier * 0.8)  # Slightly less overlap proportion
        
        # Ensure within bounds
        final_size = max(self.min_chunk_size, min(self.max_chunk_size, final_size))
        final_overlap = min(final_overlap, final_size // 3)  # Overlap shouldn't exceed 1/3 of chunk
        
        return final_size, final_overlap

    def generate_chunk_summary(self, text: str, context: str = "") -> str:
        """Generate concise summary of chunk content"""
        if not self.add_summaries or len(text) < 100:
            return ""
        
        try:
            prompt = f"""
            Aşağıdaki metni {self.summary_length} karakter civarında özetleyin. 
            Teknik terimler ve önemli kavramları koruyun.
            {context}
            
            Metin:
            {text[:1000]}...
            
            Özet:
            """
            
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            
            # Ensure summary is within length limit
            if len(summary) > self.summary_length + 50:
                summary = summary[:self.summary_length] + "..."
            
            return summary
            
        except Exception as e:
            print(f"⚠️  Summary generation failed: {e}")
            # Fallback: simple truncation
            return text[:self.summary_length] + "..." if len(text) > self.summary_length else text

    def create_enhanced_chunks(self, text: str, source: str, url: str) -> List[Dict]:
        """Create chunks with overlapping summaries and enhanced context"""
        content_type = self.detect_content_type(text)
        chunk_size, chunk_overlap = self.get_adaptive_chunk_size(content_type, len(text))
        
        # Create base chunks
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=self.separators,
            keep_separator=True,
            is_separator_regex=False
        )
        
        base_chunks = splitter.split_text(text)
        enhanced_chunks = []
        
        # Generate summaries for context
        chunk_summaries = []
        if self.add_summaries and len(base_chunks) > 1:
            print(f"📝 Generating summaries for {len(base_chunks)} chunks...")
            for i, chunk_text in enumerate(base_chunks):
                if len(chunk_text.strip()) >= self.min_chunk_size:
                    summary = self.generate_chunk_summary(
                        chunk_text, 
                        f"Bu chunk {i+1}/{len(base_chunks)} numaralı bölümdür."
                    )
                    chunk_summaries.append(summary)
                else:
                    chunk_summaries.append("")
        
        # Create enhanced chunks with context
        for i, chunk_text in enumerate(base_chunks):
            if len(chunk_text.strip()) < self.min_chunk_size:
                # Skip very small chunks unless they contain important keywords
                if not self._contains_important_keywords(chunk_text):
                    continue
            
            enhanced_text = chunk_text.strip()
            
            # Add previous chunk summary at the beginning
            if self.add_summaries and i > 0 and chunk_summaries and chunk_summaries[i-1]:
                prev_summary = f"[Önceki bölüm özeti: {chunk_summaries[i-1]}]\n\n"
                enhanced_text = prev_summary + enhanced_text
            
            # Add next chunk summary at the end
            if self.add_summaries and i < len(base_chunks) - 1 and chunk_summaries and i+1 < len(chunk_summaries) and chunk_summaries[i+1]:
                next_summary = f"\n\n[Sonraki bölüm özeti: {chunk_summaries[i+1]}]"
                enhanced_text = enhanced_text + next_summary
            
            # Create enhanced metadata
            metadata = self._create_enhanced_metadata(
                enhanced_text, source, url, content_type, i, len(base_chunks),
                chunk_size, chunk_overlap
            )
            
            enhanced_chunks.append({
                "text": enhanced_text,
                "original_text": chunk_text.strip(),  # Keep original for comparison
                "source": source,
                "url": url,
                "metadata": metadata
            })
        
        return enhanced_chunks

    def _contains_important_keywords(self, text: str) -> bool:
        """Enhanced keyword detection for important content"""
        important_keywords = [
            # Technical terms
            "api", "sdk", "implementation", "gradle", "json", "xml", "swift", "kotlin",
            # Netmera specific
            "push notification", "segment", "campaign", "netmera", "analytics", "automation",
            # Important markers
            "error", "warning", "important", "note", "tip", "critical", "required",
            # Turkish equivalents
            "hata", "uyarı", "önemli", "not", "gerekli", "kritik"
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in important_keywords)

    def _create_enhanced_metadata(self, text: str, source: str, url: str, 
                                 content_type: str, chunk_index: int, 
                                 total_chunks: int, chunk_size: int, 
                                 chunk_overlap: int) -> Dict:
        """Create comprehensive metadata for enhanced retrieval"""
        # Extract headers if present
        headers = re.findall(r'^#{1,6}\s+(.+)$', text, re.MULTILINE)
        
        # Extract code languages
        code_languages = re.findall(r'```(\w+)', text)
        
        # Detect technical terms (enhanced)
        tech_terms = []
        netmera_terms = [
            "push notification", "segment", "campaign", "sdk", "api", 
            "analytics", "automation", "journey", "gradle", "implementation",
            "firebase", "ios", "android", "swift", "kotlin", "javascript"
        ]
        
        text_lower = text.lower()
        for term in netmera_terms:
            if term in text_lower:
                tech_terms.append(term)
        
        # Enhanced content analysis
        has_links = bool(re.search(r'https?://[^\s]+', text))
        has_images = bool(re.search(r'!\[.*?\]\(.*?\)', text))
        has_tables = bool(re.search(r'\|.*\|', text))
        complexity_score = self._calculate_complexity_score(text)
        
        return {
            "content_type": content_type,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "chunk_size_used": chunk_size,
            "chunk_overlap_used": chunk_overlap,
            "char_count": len(text),
            "word_count": len(text.split()),
            "headers": headers,
            "code_languages": code_languages,
            "tech_terms": tech_terms,
            "has_code": "```" in text,
            "has_steps": bool(re.search(r'\n\d+\.', text)),
            "has_links": has_links,
            "has_images": has_images,
            "has_tables": has_tables,
            "language": self._detect_language(text),
            "complexity_score": complexity_score,
            "enhancement_features": {
                "has_prev_summary": "[Önceki bölüm özeti:" in text,
                "has_next_summary": "[Sonraki bölüm özeti:" in text,
                "is_enhanced": True
            }
        }

    def _calculate_complexity_score(self, text: str) -> float:
        """Calculate text complexity score for better chunking decisions"""
        score = 0.0
        
        # Technical indicators
        if "```" in text: score += 0.3
        if re.search(r'\{[\s\S]*\}', text): score += 0.2
        if len(re.findall(r'[A-Z][a-z]+[A-Z]', text)) > 3: score += 0.2  # CamelCase
        
        # Structure indicators
        headers_count = len(re.findall(r'^#{1,6}\s+', text, re.MULTILINE))
        if headers_count > 0: score += min(0.3, headers_count * 0.1)
        
        # List indicators
        list_items = len(re.findall(r'^\s*[-*+]\s+', text, re.MULTILINE))
        numbered_items = len(re.findall(r'^\s*\d+\.\s+', text, re.MULTILINE))
        if list_items + numbered_items > 0: score += min(0.2, (list_items + numbered_items) * 0.05)
        
        # Technical terms density
        tech_terms_count = sum(1 for term in ["api", "sdk", "json", "xml", "http"] if term in text.lower())
        score += min(0.3, tech_terms_count * 0.1)
        
        return min(1.0, score)

    def _detect_language(self, text: str) -> str:
        """Enhanced language detection"""
        turkish_chars = set('çğıöşüÇĞIİÖŞÜ')
        has_turkish = any(char in text for char in turkish_chars)
        
        turkish_words = ['ve', 'bir', 'bu', 'için', 'ile', 'olan', 'nasıl', 'nedir', 'hangi', 'nerede']
        english_words = ['the', 'and', 'or', 'how', 'what', 'with', 'from', 'that', 'which', 'where']
        
        text_lower = text.lower()
        turkish_count = sum(1 for word in turkish_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if has_turkish or turkish_count > english_count:
            return "turkish"
        return "english"

    def experiment_with_chunk_sizes(self, texts: List[Dict], 
                                   output_file: str = "data/analysis/chunk_size_experiments.json") -> Dict:
        """Experiment with different chunk sizes and evaluate results"""
        print("🔬 Running chunk size experiments...")
        
        results = {}
        
        for experiment_name, config in self.size_experiments.items():
            print(f"🧪 Testing {experiment_name} configuration...")
            
            # Temporarily adjust settings
            original_size = self.chunk_size
            original_overlap = self.chunk_overlap
            
            self.chunk_size = config["base"]
            self.chunk_overlap = config["overlap"]
            
            # Process documents
            all_chunks = []
            processing_start = time.time()
            
            for doc in texts[:10]:  # Test with first 10 docs for speed
                chunks = self.create_enhanced_chunks(doc["text"], doc["source"], doc["url"])
                all_chunks.extend(chunks)
            
            processing_time = time.time() - processing_start
            
            # Calculate metrics
            chunk_sizes = [len(chunk["text"]) for chunk in all_chunks]
            
            results[experiment_name] = {
                "config": config,
                "total_chunks": len(all_chunks),
                "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                "min_chunk_size": min(chunk_sizes) if chunk_sizes else 0,
                "max_chunk_size": max(chunk_sizes) if chunk_sizes else 0,
                "processing_time": processing_time,
                "chunks_per_second": len(all_chunks) / processing_time if processing_time > 0 else 0,
                "content_type_distribution": {}
            }
            
            # Content type distribution
            for chunk in all_chunks:
                content_type = chunk["metadata"]["content_type"]
                results[experiment_name]["content_type_distribution"][content_type] = \
                    results[experiment_name]["content_type_distribution"].get(content_type, 0) + 1
            
            # Restore original settings
            self.chunk_size = original_size
            self.chunk_overlap = original_overlap
        
        # Save results
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Experiment results saved to {output_file}")
        return results


def enhanced_chunking_pipeline(texts: List[Dict], 
                              experiment_mode: bool = False,
                              chunk_size: int = 1200,
                              add_summaries: bool = True) -> Tuple[List[Dict], Dict]:
    """
    Complete enhanced chunking pipeline
    
    Args:
        texts: List of documents with text, source, url
        experiment_mode: Whether to run chunk size experiments
        chunk_size: Base chunk size
        add_summaries: Whether to add overlapping summaries
    
    Returns:
        Tuple of (enhanced_chunks, processing_stats)
    """
    chunker = EnhancedSemanticChunker(
        chunk_size=chunk_size,
        add_summaries=add_summaries
    )
    
    # Run experiments if requested
    experiment_results = {}
    if experiment_mode:
        experiment_results = chunker.experiment_with_chunk_sizes(texts)
    
    # Process all documents with enhanced chunking
    print("🚀 Processing documents with enhanced semantic chunking...")
    start_time = time.time()
    
    all_chunks = []
    stats = {
        "original_docs": len(texts),
        "total_chunks": 0,
        "content_type_distribution": {},
        "enhancement_stats": {
            "chunks_with_prev_summary": 0,
            "chunks_with_next_summary": 0,
            "avg_enhancement_ratio": 0
        },
        "processing_time": 0,
        "experiment_results": experiment_results
    }
    
    for i, doc in enumerate(texts):
        chunks = chunker.create_enhanced_chunks(doc["text"], doc["source"], doc["url"])
        all_chunks.extend(chunks)
        
        # Update enhancement stats
        for chunk in chunks:
            if chunk["metadata"]["enhancement_features"]["has_prev_summary"]:
                stats["enhancement_stats"]["chunks_with_prev_summary"] += 1
            if chunk["metadata"]["enhancement_features"]["has_next_summary"]:
                stats["enhancement_stats"]["chunks_with_next_summary"] += 1
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  ✅ Processed {i + 1}/{len(texts)} documents")
    
    processing_time = time.time() - start_time
    stats["processing_time"] = processing_time
    stats["total_chunks"] = len(all_chunks)
    
    # Calculate enhancement ratio
    enhanced_chunks = sum(1 for chunk in all_chunks 
                         if chunk["metadata"]["enhancement_features"]["has_prev_summary"] or 
                            chunk["metadata"]["enhancement_features"]["has_next_summary"])
    stats["enhancement_stats"]["avg_enhancement_ratio"] = enhanced_chunks / len(all_chunks) if all_chunks else 0
    
    # Content type distribution
    for chunk in all_chunks:
        content_type = chunk["metadata"]["content_type"]
        stats["content_type_distribution"][content_type] = \
            stats["content_type_distribution"].get(content_type, 0) + 1
    
    print(f"✅ Enhanced chunking completed in {processing_time:.2f} seconds")
    print(f"📊 Created {len(all_chunks)} enhanced chunks from {len(texts)} documents")
    print(f"🔄 Enhancement ratio: {stats['enhancement_stats']['avg_enhancement_ratio']:.2%}")
    
    return all_chunks, stats


if __name__ == "__main__":
    print("🧠 Enhanced Semantic Chunking with Overlapping Summaries")
    print("=" * 60)
    
    # Example usage
    sample_texts = [
        {
            "text": "Sample technical documentation with code examples...",
            "source": "sample_doc.md",
            "url": "https://example.com/doc"
        }
    ]
    
    # Run enhanced chunking
    chunks, stats = enhanced_chunking_pipeline(
        sample_texts, 
        experiment_mode=True,
        add_summaries=True
    )
    
    print(f"Results: {len(chunks)} enhanced chunks created")
    print(f"Experiments: {len(stats['experiment_results'])} configurations tested")
