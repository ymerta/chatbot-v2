#!/usr/bin/env python3
"""
Create synthetic comparison content for iOS vs Android Netmera integration
"""

def generate_comparison_chunks():
    """Generate comparison-focused content chunks"""
    
    comparison_content = [
        {
            "title": "iOS vs Android Netmera SDK Integration Differences",
            "content": """
# iOS ve Android Netmera SDK Entegrasyonu Arasındaki Temel Farklar

## Dependency Management
- **iOS**: CocoaPods kullanılır. Podfile'a 'pod Netmera' eklenir.
- **Android**: Gradle kullanılır. build.gradle'a implementation 'com.netmera:netmera-android' eklenir.

## Configuration Files
- **iOS**: Info.plist dosyasında configuration yapılır
- **Android**: AndroidManifest.xml dosyasında permissions ve configuration yapılır

## Programming Languages
- **iOS**: Swift veya Objective-C kullanılır
- **Android**: Java veya Kotlin kullanılır

## Push Notification Setup
- **iOS**: APNs (Apple Push Notification service) certificate gerekir
- **Android**: FCM (Firebase Cloud Messaging) server key gerekir

## Permissions
- **iOS**: iOS 10+ için UNUserNotificationCenter kullanılır
- **Android**: INTERNET, WAKE_LOCK, RECEIVE_BOOT_COMPLETED permissions gerekir

## Build Process
- **iOS**: Xcode ile build edilir, provisioning profile gerekir
- **Android**: Android Studio ile build edilir, signing key gerekir
            """,
            "url": "netmera-ios-android-comparison",
            "source": "comparison_guide"
        },
        {
            "title": "Platform-Specific Implementation Differences",
            "content": """
# Platform-Specific Netmera Implementation Farkları

## SDK Initialization
**iOS**:
```swift
Netmera.configure(apiKey: "YOUR_API_KEY")
```

**Android**:
```java
Netmera.init(context, "YOUR_API_KEY")
```

## Push Token Registration
**iOS**: Otomatik olarak APNs token alınır ve Netmera'ya gönderilir
**Android**: FCM token alınır ve manuel olarak Netmera'ya register edilebilir

## Background Processing
**iOS**: iOS 13+ background app refresh limitations
**Android**: Doze mode ve app standby optimizations

## Deep Linking
**iOS**: URL Schemes ve Universal Links kullanılır
**Android**: Intent Filters ve App Links kullanılır

## Media Push
**iOS**: Notification Service Extension gerekir
**Android**: Direkt olarak desteklenir, extra setup gerekmez
            """,
            "url": "netmera-platform-implementation-differences", 
            "source": "comparison_guide"
        },
        {
            "title": "iOS Android Development Environment Differences",
            "content": """
# iOS ve Android Geliştirme Ortamı Farkları

## IDE Requirements
- **iOS**: Xcode (macOS gerekli), Interface Builder
- **Android**: Android Studio (cross-platform), Layout Editor

## Simulator/Emulator
- **iOS**: iOS Simulator (push notification test sınırlı)
- **Android**: Android Emulator (Google Play Services ile push test mümkün)

## Testing
- **iOS**: TestFlight ile beta testing, physical device push test
- **Android**: Google Play Console internal testing, emulator push test

## Deployment
- **iOS**: App Store submission, Apple Developer Program (ücretli)
- **Android**: Google Play Store, Google Play Console (bir kerelik ücret)

## Debugging
- **iOS**: Xcode debugger, Console.app for logs
- **Android**: Android Studio debugger, Logcat for logs

## Performance Monitoring
- **iOS**: Instruments, Xcode Organizer
- **Android**: Android Profiler, Firebase Performance
            """,
            "url": "netmera-development-environment-differences",
            "source": "comparison_guide"
        }
    ]
    
    return comparison_content

def save_comparison_files():
    """Save comparison content as separate files for indexing"""
    
    content_chunks = generate_comparison_chunks()
    
    import os
    os.makedirs("data/comparison", exist_ok=True)
    
    for i, chunk in enumerate(content_chunks):
        filename = f"data/comparison/netmera-{chunk['title'].lower().replace(' ', '-').replace('/', '-')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# {chunk['title']}\n\n")
            f.write(chunk['content'])
            f.write(f"\n\nSource: {chunk['source']}")
            f.write(f"\nURL: {chunk['url']}")
        
        print(f"✅ Created: {filename}")
    
    print(f"\n🎯 Generated {len(content_chunks)} comparison documents")
    print("📁 Location: data/comparison/")
    print("🔄 Next: Re-run FAISS indexing to include these files")

if __name__ == "__main__":
    save_comparison_files()
