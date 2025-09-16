#!/usr/bin/env python3
"""
Firebase setup script for NetmerianBot
Creates collections and sample data for testing
"""

import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def init_firebase():
    """Initialize Firebase connection"""
    try:
        # Initialize Firebase if not already done
        if not firebase_admin._apps:
            # Use service account from secrets
            cred_dict = {
                "type": "service_account",
                "project_id": st.secrets["FIREBASE_PROJECT_ID"],
                "private_key_id": st.secrets["FIREBASE_PRIVATE_KEY_ID"],
                "private_key": st.secrets["FIREBASE_PRIVATE_KEY"].replace('\\n', '\n'),
                "client_email": st.secrets["FIREBASE_CLIENT_EMAIL"],
                "client_id": st.secrets["FIREBASE_CLIENT_ID"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                "client_x509_cert_url": f"https://www.googleapis.com/robot/v1/metadata/x509/{st.secrets['FIREBASE_CLIENT_EMAIL']}"
            }
            
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        
        # Get Firestore client
        db = firestore.client()
        print("✅ Firebase connection successful")
        return db
        
    except Exception as e:
        print(f"⚠️ Firebase connection failed: {e}")
        return None

def setup_firebase():
    """Setup Firebase collections and sample data"""
    print("🚀 Setting up Firebase for NetmerianBot...")
    
    # Initialize Firebase
    db = init_firebase()
    if db is None:
        print("❌ Firebase initialization failed")
        return
    
    try:
        # Create sample unified conversation with feedback
        sample_conversation = {
            # Conversation Data
            "conversation_id": "test_conv_001",
            "user_message": "How does push notification work?",
            "assistant_response": "Push notifications work by sending messages from servers to user devices through platform-specific services like FCM (Android) or APNs (iOS). The process involves registering device tokens, sending requests to push services, and displaying notifications to users.",
            "language": "English",
            "context_docs": ["push_notification_guide.txt"],
            "timestamp": datetime.now(),
            
            # Feedback Data
            "rating": 5,
            "score": 1.0,
            "feedback_text": "Great response! Very helpful explanation.",
            "comment": "⭐ Rating: 5/5 stars\n💬 Comment: Great response! Very helpful explanation.",
            "feedback_timestamp": datetime.now(),
            "has_feedback": True,
            
            # Type
            "type": "conversation_with_feedback"
        }
        
        # Insert sample conversation
        conv_ref = db.collection('conversations').document()
        conv_ref.set(sample_conversation)
        print(f"✅ Sample unified conversation created: {conv_ref.id}")
        
        # Create another sample without feedback
        sample_conversation_no_feedback = {
            # Conversation Data
            "conversation_id": "test_conv_002",
            "user_message": "What is Netmera SDK?",
            "assistant_response": "Netmera SDK is a comprehensive mobile engagement platform that provides push notifications, in-app messaging, analytics, and user segmentation capabilities for mobile applications.",
            "language": "English",
            "context_docs": ["sdk_overview.txt"],
            "timestamp": datetime.now(),
            
            # Feedback Data (empty)
            "rating": None,
            "score": None,
            "feedback_text": "",
            "comment": "",
            "feedback_timestamp": None,
            "has_feedback": False,
            
            # Type
            "type": "conversation_with_feedback"
        }
        
        # Insert sample conversation without feedback
        conv_ref2 = db.collection('conversations').document()
        conv_ref2.set(sample_conversation_no_feedback)
        print(f"✅ Sample conversation (no feedback) created: {conv_ref2.id}")
        
        # Get collection stats
        docs = db.collection('conversations').stream()
        doc_count = len(list(docs))
        
        print(f"\n📊 Firebase Statistics:")
        print(f"   - Collection: conversations")
        print(f"   - Documents: {doc_count}")
        
        print("\n🎯 Firebase setup complete!")
        print("You can now run the NetmerianBot with Firebase feedback system.")
        
    except Exception as e:
        print(f"❌ Firebase setup error: {e}")

if __name__ == "__main__":
    setup_firebase()
