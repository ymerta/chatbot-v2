#!/usr/bin/env python3
"""
Quick FAISS Rebuild Script
Sadece FAISS index'i yeniden oluşturmak için hızlı script
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    """Hızlı FAISS rebuild"""
    print("⚡ Quick FAISS Rebuild")
    print("=" * 30)
    
    try:
        # Optimized version'ı tercih et
        print("🚀 Optimized FAISS builder kullanılıyor...")
        from faiss_builder import main as build_optimized
        
        # Optimized chunking ile rebuild
        success = build_optimized(
            chunk_size=1200,      # Optimized size
            chunk_overlap=200,    # Optimized overlap
            backup_existing=True, # Backup yap
            save_debug_chunks=False
        )
        
        if success:
            print("\n✅ FAISS index başarıyla yeniden oluşturuldu!")
            print("   Optimized chunking (1200/200) kullanıldı")
        else:
            print("\n❌ FAISS rebuild başarısız!")
            return False
            
    except ImportError:
        # Fallback: Simple version kullan
        print("⚠️  Optimized builder bulunamadı, simple version kullanılıyor...")
        
        try:
            from index_build_simple import main as build_simple
            success = build_simple(save_chunk_files=False)
            
            if success:
                print("\n✅ FAISS index yeniden oluşturuldu!")
                print("   Simple chunking (800/120) kullanıldı")
            else:
                print("\n❌ FAISS rebuild başarısız!")
                return False
                
        except ImportError as e:
            print(f"❌ FAISS builder yüklenemedi: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n🔧 Sorun giderme:")
        print("   1. Scraped dosyalar var mı? data/dev/ klasörünü kontrol edin")
        print("   2. Web scraper çalıştırın: python src/web_scraper.py")
        print("   3. API key'leri kontrol edin (OPENAI_API_KEY)")
        exit(1)
    
    print("\n🎯 Sonraki adımlar:")
    print("   1. Chatbot'u test edin: streamlit run app.py")
    print("   2. Evaluation çalıştırın: python evaluate_chatbot.py --dataset all")
    print("   3. Performance'ı karşılaştırın")
