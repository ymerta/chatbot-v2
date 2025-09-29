"""
İyileştirilmiş dil algılama sistemini test edelim
"""

def detect_lang_improved(query):
    """İyileştirilmiş dil algılama sistemi"""
    q = query.strip()
    q_lower = q.lower()
    
    # Türkçe karakterler kontrolü
    has_turkish_chars = any(ch in "çğıöşü" for ch in q_lower)
    
    # Türkçe kelimeler kontrolü (yaygın Türkçe kelimeler)
    turkish_words = [
        'nasıl', 'nedir', 'neden', 'hangi', 'için', 've', 'bir', 'bu', 'şu', 'o',
        'ile', 'olan', 'yapılır', 'kullanım', 'kurulum', 'ayar', 'sorun', 'hata',
        'nerede', 'ne', 'mi', 'mu', 'mı', 'mü', 'da', 'de', 'ta', 'te'
    ]
    has_turkish_words = any(word in q_lower for word in turkish_words)
    
    # İngilizce kelimeler kontrolü (yaygın İngilizce kelimeler)
    english_words = [
        'how', 'what', 'where', 'when', 'why', 'which', 'the', 'and', 'or', 'is',
        'are', 'can', 'will', 'should', 'would', 'could', 'setup', 'install',
        'configuration', 'error', 'problem', 'issue', 'with', 'from', 'to'
    ]
    has_english_words = any(word in q_lower for word in english_words)
    
    # Dil belirleme mantığı
    if has_turkish_chars or has_turkish_words:
        return "Türkçe"
    elif has_english_words:
        return "English"
    else:
        # Varsayılan olarak İngilizce (teknik terimler için)
        return "English"

def detect_lang_old(query):
    """Eski sistem (sadece Türkçe karakterler)"""
    return "Türkçe" if any(ch in "çğıöşü" for ch in query.lower()) else "English"

# Test sorguları
test_queries = [
    "Kafka consumer lag nasıl kontrol edilir?",    # Türkçe (nasıl)
    "How to check Kafka consumer lag?",            # İngilizce (how, to)
    "App Module architecture overview",            # İngilizce (varsayılan)
    "MongoDB performans sorunları",                # Türkçe (sorunları)
    "What is InternalDeviceService?",              # İngilizce (what, is)
    "Hazelcast lock nedir?",                       # Türkçe (nedir) ✅ FIX!
    "push notification setup",                     # İngilizce (setup)
    "bildirim kurulumu nasıl yapılır",            # Türkçe (nasıl, yapılır)
    "consumer lag problem",                        # İngilizce (problem)
    "hata ayıklama",                              # Türkçe (hata)
    "debugging tools",                            # İngilizce (varsayılan)
    "hangi platformlar destekleniyor?",           # Türkçe (hangi)
    "which platforms are supported?",             # İngilizce (which, are)
    "InternalDeviceService nedir?",               # Türkçe (nedir) ✅ FIX!
    "MongoDB connection error"                     # İngilizce (error)
]

print("🚀 İyileştirilmiş Dil Algılama Test Sonuçları")
print("=" * 65)

correct_predictions = 0
total_predictions = len(test_queries)

for query in test_queries:
    old_result = detect_lang_old(query)
    new_result = detect_lang_improved(query)
    
    # Beklenen sonuç (manuel olarak belirlenen)
    expected = "Türkçe" if any(word in query.lower() for word in 
                              ['nasıl', 'nedir', 'sorunları', 'yapılır', 'hata', 'hangi', 'destekleniyor']) else "English"
    
    is_correct = new_result == expected
    if is_correct:
        correct_predictions += 1
    
    status = "✅" if is_correct else "❌"
    improvement = "🔥 İYİLEŞTİ!" if (old_result != expected and new_result == expected) else ""
    
    print(f"\n📝 Query: '{query}'")
    print(f"   🔴 Eski: {old_result}")
    print(f"   🟢 Yeni: {new_result}")
    print(f"   🎯 Beklenen: {expected}")
    print(f"   {status} {improvement}")

accuracy = (correct_predictions / total_predictions) * 100
print(f"\n" + "=" * 65)
print(f"📊 SONUÇ:")
print(f"   ✅ Doğru tahmin: {correct_predictions}/{total_predictions}")
print(f"   🎯 Doğruluk oranı: {accuracy:.1f}%")
print(f"   🔥 Önemli düzeltmeler:")
print(f"      • 'Hazelcast lock nedir?' → Türkçe ✅")
print(f"      • 'InternalDeviceService nedir?' → Türkçe ✅")
print(f"      • Türkçe kelime tanıma eklendi")
print(f"      • İngilizce kelime tanıma eklendi")
