"""
Advanced Chunking Strategy for Netmera Documentation
Optimized for technical documentation with code examples and multilingual content
"""

import re
import os
from typing import List, Dict, Tuple
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

class OptimizedChunker:
    """Enhanced chunking strategy for technical documentation"""
    
    def __init__(self, 
                 chunk_size: int = 1200,
                 chunk_overlap: int = 200,
                 min_chunk_size: int = 100,
                 max_chunk_size: int = 2000):
        """
        Initialize optimized chunker
        
        Args:
            chunk_size: Target chunk size (increased from 800 to 1200)
            chunk_overlap: Overlap between chunks (increased from 120 to 200)
            min_chunk_size: Minimum viable chunk size
            max_chunk_size: Maximum chunk size before force splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
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
        
    def detect_content_type(self, text: str) -> str:
        """Detect the type of content for optimized chunking"""
        text_lower = text.lower()
        
        # Code-heavy content
        if ("```" in text or 
            "gradle" in text_lower or 
            "implementation" in text_lower or
            "json" in text_lower or
            re.search(r'\{[\s\S]*\}', text)):
            return "code"
        
        # API documentation
        if ("api" in text_lower or 
            "endpoint" in text_lower or
            "http" in text_lower):
            return "api"
        
        # Step-by-step guides
        if (re.search(r'\n\d+\.', text) or
            "adım" in text_lower or
            "step" in text_lower):
            return "tutorial"
        
        
        return "general"
    
    def split_code_aware(self, text: str, source: str, url: str) -> List[Dict]:
        """Split text while preserving code blocks and technical structure"""
        chunks = []
        content_type = self.detect_content_type(text)
        
        # Adjust chunk size based on content type
        if content_type == "code":
            # Larger chunks for code to preserve context
            chunk_size = min(self.max_chunk_size, self.chunk_size * 1.5)
            overlap = min(300, self.chunk_overlap * 1.5)
        elif content_type == "api":
            # Medium chunks for API docs
            chunk_size = self.chunk_size * 1.2
            overlap = self.chunk_overlap * 1.2
        elif content_type == "tutorial":
            # Keep steps together
            chunk_size = self.chunk_size * 1.3
            overlap = self.chunk_overlap * 1.1
        else:
            chunk_size = self.chunk_size
            overlap = self.chunk_overlap
        
        # Use RecursiveCharacterTextSplitter with custom separators
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=int(chunk_size),
            chunk_overlap=int(overlap),
            separators=self.separators,
            keep_separator=True,
            is_separator_regex=False
        )
        
        splits = splitter.split_text(text)
        
        for i, chunk_text in enumerate(splits):
            # Skip too small chunks unless they contain important keywords
            if (len(chunk_text) < self.min_chunk_size and 
                not self._contains_important_keywords(chunk_text)):
                continue
            
            # Create enhanced metadata
            metadata = self._create_enhanced_metadata(
                chunk_text, source, url, content_type, i, len(splits)
            )
            
            chunks.append({
                "text": chunk_text.strip(),
                "source": source,
                "url": url,
                "metadata": metadata
            })
        
        return chunks
    
    def _contains_important_keywords(self, text: str) -> bool:
        """Check if small chunk contains important technical keywords"""
        important_keywords = [
            "api", "sdk", "implementation", "gradle", "json", "xml",
            "push notification", "segment", "campaign", "netmera",
            "error", "warning", "important", "note", "tip"
        ]
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in important_keywords)
    
    def _create_enhanced_metadata(self, text: str, source: str, url: str, 
                                 content_type: str, chunk_index: int, 
                                 total_chunks: int) -> Dict:
        """Create enhanced metadata for better retrieval"""
        # Extract headers if present
        headers = re.findall(r'^#{1,6}\s+(.+)$', text, re.MULTILINE)
        
        # Extract code languages
        code_languages = re.findall(r'```(\w+)', text)
        
        # Detect technical terms
        tech_terms = []
        netmera_terms = ["push notification", "segment", "campaign", "sdk", "api", 
                        "analytics", "automation", "journey", "gradle", "implementation"]
        
        text_lower = text.lower()
        for term in netmera_terms:
            if term in text_lower:
                tech_terms.append(term)
        
        return {
            "content_type": content_type,
            "chunk_index": chunk_index,
            "total_chunks": total_chunks,
            "char_count": len(text),
            "word_count": len(text.split()),
            "headers": headers,
            "code_languages": code_languages,
            "tech_terms": tech_terms,
            "has_code": "```" in text,
            "has_steps": bool(re.search(r'\n\d+\.', text)),
            "language": self._detect_language(text)
        }
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        turkish_chars = set('çğıöşüÇĞIİÖŞÜ')
        has_turkish = any(char in text for char in turkish_chars)
        
        turkish_words = ['ve', 'bir', 'bu', 'için', 'ile', 'olan', 'nasıl', 'nedir']
        english_words = ['the', 'and', 'or', 'how', 'what', 'with', 'from', 'that']
        
        text_lower = text.lower()
        turkish_count = sum(1 for word in turkish_words if word in text_lower)
        english_count = sum(1 for word in english_words if word in text_lower)
        
        if has_turkish or turkish_count > english_count:
            return "turkish"
        return "english"

class ChunkAnalyzer:
    """Analyze existing chunks for optimization insights"""
    
    def __init__(self, faiss_store_path: str):
        self.faiss_store_path = faiss_store_path
        
    def analyze_current_chunks(self) -> Dict:
        """Analyze current FAISS store chunks"""
        try:
            emb = OpenAIEmbeddings()
            vs = FAISS.load_local(self.faiss_store_path, emb, allow_dangerous_deserialization=True)
            
            docs = vs.docstore._dict
            chunk_stats = {
                "total_chunks": len(docs),
                "sizes": [],
                "sources": {},
                "content_types": {}
            }
            
            for doc in docs.values():
                text = doc.page_content
                source = doc.metadata.get('source', 'unknown')
                
                chunk_stats["sizes"].append(len(text))
                chunk_stats["sources"][source] = chunk_stats["sources"].get(source, 0) + 1
                
                # Analyze content type
                content_type = self._detect_content_type(text)
                chunk_stats["content_types"][content_type] = chunk_stats["content_types"].get(content_type, 0) + 1
            
            # Calculate statistics
            sizes = chunk_stats["sizes"]
            chunk_stats["avg_size"] = sum(sizes) / len(sizes) if sizes else 0
            chunk_stats["min_size"] = min(sizes) if sizes else 0
            chunk_stats["max_size"] = max(sizes) if sizes else 0
            chunk_stats["median_size"] = sorted(sizes)[len(sizes)//2] if sizes else 0
            
            return chunk_stats
            
        except Exception as e:
            return {"error": str(e)}
    
    def _detect_content_type(self, text: str) -> str:
        """Simple content type detection"""
        text_lower = text.lower()
        
        if "```" in text or "gradle" in text_lower:
            return "code"
        elif "api" in text_lower:
            return "api"
        elif re.search(r'\n\d+\.', text):
            return "tutorial"
        else:
            return "general"

def optimize_chunking_strategy(texts: List[Dict], 
                             chunk_size: int = 1200,
                             chunk_overlap: int = 200) -> Tuple[List[Dict], Dict]:
    """
    Optimize chunking strategy for the given texts
    
    Args:
        texts: List of documents with text, source, url
        chunk_size: Target chunk size
        chunk_overlap: Overlap between chunks
    
    Returns:
        Tuple of (optimized_chunks, optimization_stats)
    """
    chunker = OptimizedChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    
    all_chunks = []
    stats = {
        "original_docs": len(texts),
        "total_chunks": 0,
        "content_type_distribution": {},
        "average_chunk_size": 0,
        "chunks_by_source": {}
    }
    
    for doc in texts:
        chunks = chunker.split_code_aware(doc["text"], doc["source"], doc["url"])
        all_chunks.extend(chunks)
        
        # Update stats
        source = doc["source"]
        stats["chunks_by_source"][source] = stats["chunks_by_source"].get(source, 0) + len(chunks)
        
        for chunk in chunks:
            content_type = chunk["metadata"]["content_type"]
            stats["content_type_distribution"][content_type] = \
                stats["content_type_distribution"].get(content_type, 0) + 1
    
    stats["total_chunks"] = len(all_chunks)
    if all_chunks:
        stats["average_chunk_size"] = sum(len(chunk["text"]) for chunk in all_chunks) / len(all_chunks)
    
    return all_chunks, stats

# Configuration presets for different use cases
CHUNKING_PRESETS = {
    "balanced": {
        "chunk_size": 1200,
        "chunk_overlap": 200,
        "description": "Balanced approach for mixed content"
    },
    "code_heavy": {
        "chunk_size": 1500,
        "chunk_overlap": 250,
        "description": "Optimized for code-heavy documentation"
    },
    "tutorial_focused": {
        "chunk_size": 1400,
        "chunk_overlap": 220,
        "description": "Optimized for step-by-step tutorials"
    }
}

if __name__ == "__main__":
    print("🔧 Optimized Chunking Strategy for Netmera Documentation")
    print("=" * 60)
    print("Available presets:")
    for name, config in CHUNKING_PRESETS.items():
        print(f"  - {name}: {config['description']}")
        print(f"    Chunk size: {config['chunk_size']}, Overlap: {config['chunk_overlap']}")
