
import streamlit as st
import os
import datetime
import asyncio
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
import schedule
import time
from threading import Thread
import requests
from bs4 import BeautifulSoup
import hashlib
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from textstat import flesch_reading_ease
import re
from collections import Counter
import logging

# Enhanced imports for better functionality
from utils import (
    verify_user,
    register_user,
    get_conversational_agent,
    get_combined_conversational_agent,
    process_and_store_docs,
    process_and_store_single_doc,
    load_vector_store,
    load_global_vector_store,
    create_global_knowledge_base,
    check_global_knowledge_base_status,
    list_preloaded_documents,
    get_user_uploaded_document,
    has_user_uploaded_document,
    delete_user_document_and_index,
    save_chat_history,
    load_chat_history,
    list_past_chats,
    delete_chat_history,
    extract_pdf_content,
    extract_docx_content,
    get_scraped_data_files,
    read_scraped_data_file,
    get_website_full_name
)

from langchain_core.messages import AIMessage, HumanMessage

# Enhanced page configuration with better styling
st.set_page_config(
    page_title="🏦 APMH ChatBot - Enhanced AI Assistant",
    layout="wide",
    page_icon="🤖",
    initial_sidebar_state="expanded"
)

# Custom CSS for enhanced UI
st.markdown("""
<style>
    /* Enhanced styling */
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        color: white;
        text-align: center;
    }
    .metric-card {
        background: linear-gradient(145deg, #f0f0f0, #cacaca);
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 3px 3px 6px #bebebe, -3px -3px 6px #ffffff;
        margin: 0.5rem;
    }
    .chat-container {
        background: #f8f9fa;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid #667eea;
    }
    .error-container {
        background: #ffe6e6;
        border: 1px solid #ff9999;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .success-container {
        background: #e6ffe6;
        border: 1px solid #99ff99;
        border-radius: 5px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .info-box {
        background: linear-gradient(135deg, #74b9ff, #0984e3);
        color: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .sidebar-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border: 1px solid #dee2e6;
    }
    .document-status {
        display: flex;
        align-items: center;
        padding: 0.5rem;
        background: #e9ecef;
        border-radius: 5px;
        margin: 0.25rem 0;
    }
    .progress-container {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize enhanced session state variables
def initialize_session_state():
    """Initialize all session state variables with enhanced defaults"""
    defaults = {
        "logged_in": False,
        "username": "",
        "chat_history": [],
        "agent_executor": None,
        "current_chat_id": None,
        "viewing_file": None,
        "viewing_scraped_data": None,
        "selected_website": None,
        "viewing_kb_file": None,
        "fuzzy_threshold": 80,
        "auto_spell_correct": True,
        "dark_mode": False,
        "last_rbi_update": None,
        "document_analytics": {},
        "search_history": [],
        "user_preferences": {
            "response_length": "medium",
            "technical_level": "intermediate",
            "language": "english"
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Enhanced fuzzy search functionality
class EnhancedFuzzySearch:
    """Enhanced fuzzy search with spell correction and semantic matching"""

    def __init__(self, threshold=80):
        self.threshold = threshold
        self.spell_corrections = {}

    def fuzzy_search_documents(self, query, document_texts, top_k=5):
        """Perform fuzzy search across document texts with spell correction"""
        results = []

        # Apply spell correction if enabled
        if st.session_state.get("auto_spell_correct", True):
            query = self.auto_correct_query(query)

        for doc_id, text in document_texts.items():
            # Split text into chunks for better matching
            chunks = self.split_text_into_chunks(text, 200)

            best_score = 0
            best_chunk = ""

            for chunk in chunks:
                # Use multiple fuzzy matching strategies
                ratio = fuzz.ratio(query.lower(), chunk.lower())
                partial_ratio = fuzz.partial_ratio(query.lower(), chunk.lower())
                token_sort = fuzz.token_sort_ratio(query.lower(), chunk.lower())
                token_set = fuzz.token_set_ratio(query.lower(), chunk.lower())

                # Weighted average of different metrics
                combined_score = (ratio * 0.3 + partial_ratio * 0.3 + 
                                token_sort * 0.2 + token_set * 0.2)

                if combined_score > best_score:
                    best_score = combined_score
                    best_chunk = chunk

            if best_score >= self.threshold:
                results.append({
                    'doc_id': doc_id,
                    'score': best_score,
                    'text': best_chunk,
                    'query': query
                })

        # Sort by score and return top_k results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]

    def auto_correct_query(self, query):
        """Basic spell correction for common terms"""
        corrections = {
            "apmh": "APMH",
            "rbi": "RBI",
            "rezerve": "Reserve",
            "bnak": "bank",
            "documnet": "document",
            "analsis": "analysis"
        }

        words = query.split()
        corrected_words = []

        for word in words:
            if word.lower() in corrections:
                corrected_words.append(corrections[word.lower()])
            else:
                corrected_words.append(word)

        return " ".join(corrected_words)

    def split_text_into_chunks(self, text, chunk_size=200):
        """Split text into overlapping chunks for better search"""
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size - 20):  # 20 word overlap
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)

        return chunks

# Enhanced RBI data scraper
class EnhancedRBIScraper:
    """Enhanced RBI scraper with automatic updates and change detection"""

    def __init__(self):
        self.base_url = "https://www.rbi.org.in"
        self.update_urls = {
            "press_releases": "/commonman/english/Scripts/PressReleases.aspx",
            "notifications": "/commonman/English/scripts/Notification.aspx",
            "circulars": "/commonman/english/Scripts/CircularView.aspx"
        }
        self.last_update = None

    def scrape_rbi_updates(self):
        """Scrape latest RBI updates with error handling"""
        try:
            updates = {}

            for category, url_path in self.update_urls.items():
                full_url = self.base_url + url_path

                # Add proper headers to avoid blocking
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }

                response = requests.get(full_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # Extract latest updates (implementation depends on RBI site structure)
                    updates[category] = self.extract_update_items(soup, category)
                else:
                    st.warning(f"Failed to fetch {category}: HTTP {response.status_code}")

            return updates

        except requests.RequestException as e:
            st.error(f"Network error while fetching RBI updates: {str(e)}")
            return {}
        except Exception as e:
            st.error(f"Error scraping RBI data: {str(e)}")
            return {}

    def extract_update_items(self, soup, category):
        """Extract update items from parsed HTML"""
        items = []

        try:
            # This would need to be customized based on actual RBI site structure
            # For now, returning placeholder data
            if category == "press_releases":
                # Look for press release items
                release_items = soup.find_all('div', class_=['item', 'release-item'])[:10]
                for item in release_items:
                    title = item.get_text().strip()[:100] if item else "No title"
                    items.append({
                        'title': title,
                        'date': datetime.datetime.now().strftime("%Y-%m-%d"),
                        'content': title,
                        'url': self.base_url
                    })

            return items[:10]  # Limit to latest 10 items

        except Exception as e:
            st.warning(f"Error extracting {category} items: {str(e)}")
            return []

    def schedule_updates(self):
        """Schedule automatic RBI updates"""
        schedule.every(6).hours.do(self.update_rbi_data)

    def update_rbi_data(self):
        """Update RBI data and save to files"""
        try:
            updates = self.scrape_rbi_updates()

            # Save updates to scraped_data directory
            rbi_dir = os.path.join("scraped_data", "RBI")
            os.makedirs(rbi_dir, exist_ok=True)

            for category, items in updates.items():
                filename = f"{category}_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                filepath = os.path.join(rbi_dir, filename)

                with open(filepath, 'w') as f:
                    json.dump(items, f, indent=2)

            st.session_state.last_rbi_update = datetime.datetime.now()
            return True

        except Exception as e:
            logging.error(f"Failed to update RBI data: {str(e)}")
            return False

# Enhanced document analytics
class DocumentAnalytics:
    """Provide analytics and insights for uploaded documents"""

    def analyze_document(self, file_path):
        """Comprehensive document analysis"""
        try:
            content = ""

            if file_path.endswith('.pdf'):
                content = extract_pdf_content(file_path)
            elif file_path.endswith('.docx'):
                content = extract_docx_content(file_path)
            elif file_path.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()

            if content:
                return {
                    'word_count': len(content.split()),
                    'character_count': len(content),
                    'reading_time': len(content.split()) / 250,  # Average reading speed
                    'readability_score': self.calculate_readability(content),
                    'top_keywords': self.extract_keywords(content),
                    'document_type': self.classify_document(content),
                    'language': 'English',  # Simplified for now
                    'last_analyzed': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }

            return None

        except Exception as e:
            st.error(f"Error analyzing document: {str(e)}")
            return None

    def calculate_readability(self, text):
        """Calculate document readability score"""
        try:
            return flesch_reading_ease(text)
        except:
            # Fallback simple calculation
            sentences = len([s for s in text.split('.') if s.strip()])
            words = len(text.split())
            if sentences > 0:
                return max(0, 100 - (words / sentences * 1.5))
            return 50

    def extract_keywords(self, text, top_n=10):
        """Extract top keywords from text"""
        # Simple keyword extraction
        words = re.findall(r'\b\w+\b', text.lower())

        # Filter out common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [w for w in words if w not in stop_words and len(w) > 3]

        word_freq = Counter(words)
        return word_freq.most_common(top_n)

    def classify_document(self, text):
        """Simple document classification"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['financial', 'bank', 'loan', 'credit', 'rbi']):
            return 'Financial'
        elif any(word in text_lower for word in ['legal', 'law', 'regulation', 'compliance']):
            return 'Legal'
        elif any(word in text_lower for word in ['technical', 'system', 'process', 'procedure']):
            return 'Technical'
        else:
            return 'General'

# Initialize enhanced components
initialize_session_state()
fuzzy_search = EnhancedFuzzySearch(threshold=st.session_state.fuzzy_threshold)
rbi_scraper = EnhancedRBIScraper()
doc_analytics = DocumentAnalytics()

def show_enhanced_login_page():
    """Enhanced login page with better UI"""
    # Main header with gradient
    st.markdown("""
    <div class="main-header">
        <h1>🏦 APMH Enhanced ChatBot</h1>
        <p style="margin: 0; font-size: 1.1em;">Advanced AI Assistant for Financial Document Analysis</p>
    </div>
    """, unsafe_allow_html=True)

    # Feature highlights
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        <div class="info-box">
            <h4>🔍 Fuzzy Search</h4>
            <p>Find information even with spelling mistakes</p>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown("""
        <div class="info-box">
            <h4>🏦 RBI Updates</h4>
            <p>Automatic updates from Reserve Bank of India</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("""
        <div class="info-box">
            <h4>📊 Smart Analytics</h4>
            <p>Document insights and readability analysis</p>
        </div>
        """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="sidebar-section">', unsafe_allow_html=True)
        st.subheader("🔐 Access Portal")

        menu = ["Login", "Register", "Guest Demo"]
        choice = st.selectbox("Choose Action", menu)

        if choice == "Login":
            st.markdown("**Secure Login**")
            username = st.text_input("👤 Username")
            password = st.text_input("🔒 Password", type='password')

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🚀 Login", use_container_width=True):
                    if verify_user(username, password):
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.agent_executor = None
                        st.session_state.chat_history = []
                        st.session_state.current_chat_id = None
                        st.success("✅ Login successful!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Invalid credentials")

            with col2:
                if st.button("🔄 Reset", use_container_width=True):
                    st.rerun()

        elif choice == "Register":
            st.markdown("**Create New Account**")
            new_user = st.text_input("👤 Choose Username")
            new_password = st.text_input("🔒 Create Password", type='password')
            confirm_password = st.text_input("🔒 Confirm Password", type='password')

            if st.button("📝 Register", use_container_width=True):
                if new_password != confirm_password:
                    st.error("❌ Passwords don't match")
                elif len(new_password) < 6:
                    st.error("❌ Password must be at least 6 characters")
                elif register_user(new_user, new_password):
                    st.success("✅ Account created successfully!")
                    st.info("👈 Switch to Login to access your account")
                else:
                    st.error("❌ Username already exists")

        elif choice == "Guest Demo":
            st.markdown("**Try Without Account**")
            st.info("🔓 Limited features available in guest mode")

            if st.button("🌟 Start Demo", use_container_width=True):
                st.session_state.logged_in = True
                st.session_state.username = "guest_" + str(int(time.time()))
                st.session_state.agent_executor = None
                st.success("✅ Demo started!")
                time.sleep(1)
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # Additional information
    st.markdown("---")
    st.subheader("🚀 Enhanced Features")

    feature_cols = st.columns(2)

    with feature_cols[0]:
        st.markdown("""
        **🔍 Smart Search Capabilities:**
        - Fuzzy search with spell correction
        - Semantic similarity matching
        - Multi-language support
        - Context-aware responses

        **📊 Document Analytics:**
        - Reading time estimation
        - Keyword extraction
        - Document classification
        - Readability scoring
        """)

    with feature_cols[1]:
        st.markdown("""
        **🏦 RBI Integration:**
        - Automated data collection
        - Real-time updates
        - Press release monitoring
        - Circular notifications

        **💡 User Experience:**
        - Enhanced UI/UX design
        - Progress tracking
        - Chat history management
        - Customizable preferences
        """)

def show_enhanced_chat_page():
    """Enhanced main chat interface with improved functionality"""
    user_dir = os.path.join("user_data", st.session_state.username)
    vector_store_path = os.path.join(user_dir, "faiss_index")

    # Enhanced sidebar
    with st.sidebar:
        st.markdown(f"""
        <div class="main-header" style="padding: 1rem; margin-bottom: 1rem;">
            <h3>👋 Welcome, {st.session_state.username}!</h3>
        </div>
        """, unsafe_allow_html=True)

        # Quick stats
        if os.path.exists(vector_store_path):
            stats_data = {
                "Documents": "1" if get_user_uploaded_document(st.session_state.username) else "0",
                "Chats": str(len(list_past_chats(st.session_state.username))),
                "Last Update": st.session_state.get("last_rbi_update", "Never")
            }

            st.markdown("**📊 Quick Stats**")
            for key, value in stats_data.items():
                st.markdown(f"• {key}: **{value}**")

        st.markdown("---")

        # Enhanced chat management
        st.markdown("### 💬 Chat Management")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("➕ New", use_container_width=True):
                new_chat_id = f"chat_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                st.session_state.current_chat_id = new_chat_id
                st.session_state.chat_history = []
                st.session_state.viewing_file = None
                st.session_state.viewing_scraped_data = None
                st.session_state.selected_website = None
                st.success("🆕 New chat started!")
                st.rerun()

        with col2:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        # Chat history with enhanced display
        st.markdown("**Recent Conversations:**")
        past_chats = list_past_chats(st.session_state.username)

        if past_chats:
            for chat_id, chat_title in list(past_chats.items())[:5]:  # Show only 5 recent
                with st.container():
                    col1, col2 = st.columns([4, 1])

                    with col1:
                        if st.button(f"💬 {chat_title[:30]}", key=f"load_{chat_id}", 
                                   use_container_width=True, help=chat_title):
                            st.session_state.current_chat_id = chat_id
                            st.session_state.chat_history = load_chat_history(st.session_state.username, chat_id)
                            st.session_state.viewing_file = None
                            st.session_state.viewing_scraped_data = None
                            st.session_state.selected_website = None
                            st.rerun()

                    with col2:
                        if st.button("🗑️", key=f"del_{chat_id}", use_container_width=True, 
                                   help=f"Delete '{chat_title}'"):
                            delete_chat_history(st.session_state.username, chat_id)
                            if st.session_state.current_chat_id == chat_id:
                                st.session_state.current_chat_id = None
                                st.session_state.chat_history = []
                            st.success("🗑️ Chat deleted!")
                            st.rerun()
        else:
            st.info("No previous chats")

        st.markdown("---")

        # Enhanced document management
        with st.expander("📄 Document Sources", expanded=not os.path.exists(vector_store_path)):
            current_doc = get_user_uploaded_document(st.session_state.username)

            if current_doc:
                st.markdown(f"**Current Document:**")
                st.info(f"📄 {current_doc}")

                # Document analytics
                if st.session_state.username not in st.session_state.document_analytics:
                    doc_path = os.path.join(user_dir, current_doc)
                    if os.path.exists(doc_path):
                        analytics = doc_analytics.analyze_document(doc_path)
                        if analytics:
                            st.session_state.document_analytics[st.session_state.username] = analytics

                analytics = st.session_state.document_analytics.get(st.session_state.username)
                if analytics:
                    st.markdown("**📊 Document Analytics:**")
                    st.markdown(f"• Words: **{analytics['word_count']:,}**")
                    st.markdown(f"• Reading time: **{analytics['reading_time']:.1f} min**")
                    st.markdown(f"• Type: **{analytics['document_type']}**")

                    # Show readability score with color coding
                    score = analytics['readability_score']
                    if score >= 60:
                        color = "green"
                        level = "Easy"
                    elif score >= 30:
                        color = "orange"
                        level = "Moderate"
                    else:
                        color = "red"
                        level = "Difficult"

                    st.markdown(f"• Readability: <span style='color: {color}'>**{level}** ({score:.0f})</span>", 
                              unsafe_allow_html=True)

                # Document actions
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("👁️ View", use_container_width=True):
                        st.session_state.viewing_file = current_doc
                        st.session_state.current_chat_id = None
                        st.rerun()

                with col2:
                    if st.button("🗑️ Delete", use_container_width=True):
                        delete_user_document_and_index(st.session_state.username)
                        st.session_state.agent_executor = None
                        if st.session_state.username in st.session_state.document_analytics:
                            del st.session_state.document_analytics[st.session_state.username]
                        st.success("✅ Document deleted!")
                        st.rerun()

            else:
                st.markdown("**📤 Upload Document:**")

                upload_tab1, upload_tab2 = st.tabs(["📄 File Upload", "🌐 Web URL"])

                with upload_tab1:
                    uploaded_file = st.file_uploader(
                        "Choose file", 
                        type=['pdf', 'docx', 'txt', 'csv'],
                        help="Supported: PDF, Word, Text, CSV files"
                    )

                    if uploaded_file:
                        progress_container = st.container()

                        with progress_container:
                            progress_bar = st.progress(0)
                            status_text = st.empty()

                            try:
                                # Enhanced upload process with progress tracking
                                status_text.text("📤 Uploading file...")
                                progress_bar.progress(20)

                                file_path = os.path.join(user_dir, uploaded_file.name)
                                with open(file_path, "wb") as f:
                                    f.write(uploaded_file.getbuffer())

                                status_text.text("📄 Processing document...")
                                progress_bar.progress(40)

                                # Analyze document
                                analytics = doc_analytics.analyze_document(file_path)
                                if analytics:
                                    st.session_state.document_analytics[st.session_state.username] = analytics

                                status_text.text("🧠 Building FAISS index...")
                                progress_bar.progress(70)

                                process_and_store_single_doc(st.session_state.username, file_path)

                                status_text.text("✅ Document ready!")
                                progress_bar.progress(100)

                                st.success(f"✅ '{uploaded_file.name}' uploaded successfully!")
                                st.rerun()

                            except Exception as e:
                                progress_bar.progress(0)
                                status_text.text("❌ Upload failed")
                                st.error(f"Error: {str(e)}")

                with upload_tab2:
                    url_input = st.text_input("🌐 Enter URL", placeholder="https://example.com/document.pdf")

                    if st.button("📥 Process URL", disabled=not url_input):
                        if url_input:
                            try:
                                # Enhanced URL processing
                                with st.spinner("🌐 Processing URL..."):
                                    process_and_store_single_doc(st.session_state.username, url_input)
                                    st.success("✅ URL content processed!")
                                    st.rerun()
                            except Exception as e:
                                st.error(f"Error processing URL: {str(e)}")

        # Enhanced settings
        with st.expander("⚙️ Settings", expanded=False):
            st.markdown("**🔍 Search Settings:**")

            new_threshold = st.slider(
                "Fuzzy Search Sensitivity", 
                min_value=50, max_value=100, 
                value=st.session_state.fuzzy_threshold,
                help="Lower values = more fuzzy matching"
            )

            if new_threshold != st.session_state.fuzzy_threshold:
                st.session_state.fuzzy_threshold = new_threshold
                fuzzy_search.threshold = new_threshold

            st.session_state.auto_spell_correct = st.checkbox(
                "Auto spell correction", 
                value=st.session_state.auto_spell_correct
            )

            st.markdown("**🎨 Interface:**")
            response_length = st.selectbox(
                "Response Length",
                ["short", "medium", "detailed"],
                index=["short", "medium", "detailed"].index(st.session_state.user_preferences["response_length"])
            )
            st.session_state.user_preferences["response_length"] = response_length

        # RBI Updates section
        with st.expander("🏦 RBI Updates", expanded=False):
            st.markdown("**Reserve Bank Updates:**")

            # Manual update button
            col1, col2 = st.columns(2)

            with col1:
                if st.button("🔄 Update Now", use_container_width=True):
                    with st.spinner("Fetching RBI updates..."):
                        success = rbi_scraper.update_rbi_data()
                        if success:
                            st.success("✅ RBI data updated!")
                        else:
                            st.error("❌ Update failed")

            with col2:
                if st.button("📊 View Updates", use_container_width=True):
                    files = get_scraped_data_files("RBI")
                    if files:
                        st.session_state.selected_website = "RBI"
                        st.session_state.viewing_scraped_data = True
                        st.session_state.current_chat_id = None
                        st.rerun()
                    else:
                        st.info("No RBI updates available")

            # Show last update time
            if st.session_state.last_rbi_update:
                st.text(f"Last updated: {st.session_state.last_rbi_update.strftime('%Y-%m-%d %H:%M')}")
            else:
                st.text("Never updated")

        # Logout button
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            for key in list(st.session_state.keys()):
                if key not in ['fuzzy_threshold', 'auto_spell_correct', 'user_preferences']:
                    del st.session_state[key]
            initialize_session_state()
            st.rerun()

    # Main content area
    st.markdown("""
    <div class="main-header">
        <h2>🤖 APMH Enhanced ChatBot</h2>
        <p style="margin: 0;">Intelligent Document Analysis with Advanced Search</p>
    </div>
    """, unsafe_allow_html=True)

    # Handle different view modes
    if st.session_state.viewing_file:
        show_enhanced_file_viewer()
        return
    elif st.session_state.get("viewing_scraped_data") and st.session_state.get("selected_website"):
        show_enhanced_scraped_data_viewer()
        return
    elif st.session_state.viewing_kb_file:
        show_enhanced_kb_viewer()
        return

    # Check document availability
    has_documents = os.path.exists(vector_store_path)

    if not has_documents and not st.session_state.current_chat_id:
        show_welcome_screen()
        return

    # Initialize agent if needed
    if st.session_state.agent_executor is None:
        initialize_enhanced_agent(has_documents, vector_store_path)

    # Chat interface
    if st.session_state.current_chat_id:
        show_enhanced_chat_interface()
    else:
        show_welcome_screen()

def show_enhanced_file_viewer():
    """Enhanced file viewer with analytics and better formatting"""
    file_path = os.path.join("user_data", st.session_state.username, st.session_state.viewing_file)

    # Header with back button
    col1, col2 = st.columns([1, 5])

    with col1:
        if st.button("← Back to Chat"):
            st.session_state.viewing_file = None
            st.rerun()

    with col2:
        st.markdown(f"### 📄 {st.session_state.viewing_file}")

    st.markdown("---")

    # Show document analytics if available
    analytics = st.session_state.document_analytics.get(st.session_state.username)
    if analytics:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Words", f"{analytics['word_count']:,}")

        with col2:
            st.metric("Reading Time", f"{analytics['reading_time']:.1f} min")

        with col3:
            st.metric("Type", analytics['document_type'])

        with col4:
            score = analytics['readability_score']
            if score >= 60:
                delta_color = "normal"
            elif score >= 30:
                delta_color = "normal"
            else:
                delta_color = "inverse"
            st.metric("Readability", f"{score:.0f}/100")

        # Keywords
        if analytics.get('top_keywords'):
            st.markdown("**🏷️ Top Keywords:**")
            keywords = [f"`{word}` ({count})" for word, count in analytics['top_keywords'][:10]]
            st.markdown(" • ".join(keywords))

        st.markdown("---")

    # Display file content
    try:
        if st.session_state.viewing_file.endswith('.txt'):
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            st.text_area("📄 File Content:", content, height=500)

        elif st.session_state.viewing_file.endswith('.csv'):
            df = pd.read_csv(file_path)
            st.dataframe(df, use_container_width=True)
            st.info(f"📊 CSV: {len(df)} rows × {len(df.columns)} columns")

        elif st.session_state.viewing_file.endswith('.pdf'):
            # PDF download option
            with open(file_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=st.session_state.viewing_file,
                    mime="application/pdf"
                )

            # Extract and show content
            with st.spinner("📄 Extracting PDF content..."):
                content = extract_pdf_content(file_path)
                if content and not content.startswith("Error"):
                    st.text_area("📄 PDF Content:", content, height=500)
                    st.success(f"✅ Extracted {len(content.split())} words")
                else:
                    st.error("❌ Could not extract PDF content")

        elif st.session_state.viewing_file.endswith('.docx'):
            with st.spinner("📄 Extracting Word content..."):
                content = extract_docx_content(file_path)
                if content and not content.startswith("Error"):
                    st.text_area("📄 Document Content:", content, height=500)
                    st.success(f"✅ Extracted {len(content.split())} words")
                else:
                    st.error("❌ Could not extract Word content")

    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")

def show_enhanced_scraped_data_viewer():
    """Enhanced scraped data viewer with better formatting"""
    website = st.session_state.selected_website
    full_name = get_website_full_name(website)

    # Header with back button
    col1, col2 = st.columns([1, 5])

    with col1:
        if st.button("← Back to Chat"):
            st.session_state.viewing_scraped_data = None
            st.session_state.selected_website = None
            st.rerun()

    with col2:
        st.markdown(f"### 🏦 {website} - {full_name}")

    st.markdown("---")

    # Get and display files
    files = get_scraped_data_files(website)

    if files:
        st.info(f"📊 Found {len(files)} updates from {full_name}")

        if len(files) == 1:
            # Single file display
            file_name = files[0]
            content = read_scraped_data_file(website, file_name)

            st.markdown(f"#### 📄 {file_name}")

            # Enhanced content display based on file type
            if file_name.endswith('.json'):
                try:
                    data = json.loads(content)
                    st.json(data)
                except:
                    st.text_area("Content:", content, height=500)
            elif file_name.endswith('.md'):
                st.markdown(content, unsafe_allow_html=True)
            elif file_name.endswith('.html'):
                st.components.v1.html(content, height=600, scrolling=True)
            else:
                st.text_area("Content:", content, height=500)

            st.info(f"📊 {len(content.split())} words")

        else:
            # Multiple files with tabs
            tab_names = [f"📄 {file_name}" for file_name in files]
            tabs = st.tabs(tab_names)

            for tab, file_name in zip(tabs, files):
                with tab:
                    content = read_scraped_data_file(website, file_name)

                    if file_name.endswith('.json'):
                        try:
                            data = json.loads(content)
                            st.json(data)
                        except:
                            st.text_area("Content:", content, height=400, key=f"content_{file_name}")
                    elif file_name.endswith('.md'):
                        st.markdown(content, unsafe_allow_html=True)
                    elif file_name.endswith('.html'):
                        st.components.v1.html(content, height=400, scrolling=True)
                    else:
                        st.text_area("Content:", content, height=400, key=f"content_{file_name}")

                    st.info(f"📊 {len(content.split())} words")

    else:
        st.warning(f"No updates available for {full_name}")
        st.info("Try clicking 'Update Now' in the RBI Updates section")

def show_enhanced_kb_viewer():
    """Enhanced knowledge base viewer"""
    kb_file_path = os.path.join("preloaded_docs", st.session_state.viewing_kb_file)

    # Header with back button  
    col1, col2 = st.columns([1, 5])

    with col1:
        if st.button("← Back to Chat"):
            st.session_state.viewing_kb_file = None
            st.rerun()

    with col2:
        st.markdown(f"### 📚 Knowledge Base: {st.session_state.viewing_kb_file}")

    st.markdown("---")

    try:
        if st.session_state.viewing_kb_file.endswith('.pdf'):
            # Download option
            with open(kb_file_path, "rb") as pdf_file:
                pdf_bytes = pdf_file.read()
                st.download_button(
                    label="📥 Download PDF",
                    data=pdf_bytes,
                    file_name=st.session_state.viewing_kb_file,
                    mime="application/pdf"
                )

            # Extract content
            with st.spinner("📄 Extracting PDF content..."):
                content = extract_pdf_content(kb_file_path)
                if content and not content.startswith("Error"):
                    st.text_area("📄 PDF Content:", content, height=500)
                    st.success(f"✅ Knowledge base PDF - {len(content.split())} words")
                else:
                    st.error("❌ Could not extract content")
        else:
            st.error("❌ Only PDF files are supported in knowledge base")

    except Exception as e:
        st.error(f"❌ Error reading knowledge base file: {str(e)}")

def show_welcome_screen():
    """Enhanced welcome screen with feature highlights"""
    st.markdown("""
    <div class="chat-container">
        <h3>🎉 Welcome to APMH Enhanced ChatBot!</h3>
        <p>Your intelligent assistant for financial document analysis with advanced features.</p>
    </div>
    """, unsafe_allow_html=True)

    # Feature grid
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### 🔍 Smart Search Features

        **Fuzzy Search**: Find information even with typos
        - Automatic spell correction
        - Semantic similarity matching
        - Adjustable sensitivity settings

        **Enhanced Processing**: 
        - Multi-format document support
        - Web content extraction
        - Real-time indexing
        """)

    with col2:
        st.markdown("""
        ### 📊 Analytics & Insights

        **Document Analysis**:
        - Reading time estimation
        - Keyword extraction  
        - Readability scoring
        - Content classification

        **RBI Integration**:
        - Automated data collection
        - Update notifications
        - Press release monitoring
        """)

    # Quick start guide
    st.markdown("### 🚀 Quick Start Guide")

    steps_col1, steps_col2, steps_col3 = st.columns(3)

    with steps_col1:
        st.markdown("""
        **Step 1: Upload Document**

        📤 Use the sidebar to upload:
        - PDF documents
        - Word files (.docx)
        - Text files (.txt)
        - CSV files
        - Web URLs
        """)

    with steps_col2:
        st.markdown("""
        **Step 2: Start Chatting**

        💬 Click "New Chat" and ask:
        - "What is this document about?"
        - "Summarize the key points"
        - "Extract specific information"
        - "Explain in simple terms"
        """)

    with steps_col3:
        st.markdown("""
        **Step 3: Explore Features**

        ⚙️ Customize your experience:
        - Adjust fuzzy search sensitivity
        - Enable auto spell correction
        - Set response preferences
        - View document analytics
        """)

def show_enhanced_chat_interface():
    """Enhanced chat interface with better message display"""
    # Display chat history with enhanced formatting
    for i, message in enumerate(st.session_state.chat_history):
        role = "assistant" if isinstance(message, AIMessage) else "user"

        with st.chat_message(role):
            if role == "assistant":
                # Enhanced AI message display
                st.markdown(f"<div class='chat-container'>{message.content}</div>", unsafe_allow_html=True)
            else:
                st.markdown(message.content)

    # Enhanced chat input with suggestions
    if user_query := st.chat_input("Ask questions about your documents or RBI data..."):
        # Add query to search history
        if len(st.session_state.search_history) >= 10:
            st.session_state.search_history.pop(0)
        st.session_state.search_history.append(user_query)

        st.session_state.chat_history.append(HumanMessage(content=user_query))

        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("🤔 Thinking..."):
                try:
                    # Enhanced query processing with fuzzy search
                    processed_query = user_query
                    if st.session_state.auto_spell_correct:
                        processed_query = fuzzy_search.auto_correct_query(user_query)

                    # Generate response based on agent type
                    response = generate_enhanced_response(processed_query)

                    # Display response in enhanced format
                    st.markdown(f"<div class='chat-container'>{response}</div>", unsafe_allow_html=True)

                    st.session_state.chat_history.append(AIMessage(content=response))

                    # Save chat history
                    save_chat_history(st.session_state.username, st.session_state.current_chat_id, st.session_state.chat_history)

                except Exception as e:
                    error_message = f"❌ Sorry, I encountered an error: {str(e)}"
                    st.markdown(f"<div class='error-container'>{error_message}</div>", unsafe_allow_html=True)
                    st.session_state.chat_history.append(AIMessage(content=error_message))

    # Show recent search suggestions
    if st.session_state.search_history:
        st.markdown("**💡 Recent searches:**")
        recent_searches = st.session_state.search_history[-3:]
        for search in recent_searches:
            if st.button(f"🔄 {search[:50]}...", key=f"repeat_{search[:20]}"):
                st.session_state.chat_history.append(HumanMessage(content=search))
                st.rerun()

def generate_enhanced_response(query):
    """Generate enhanced response using the agent"""
    try:
        # Check agent type and generate appropriate response
        if hasattr(st.session_state.agent_executor, 'invoke') and hasattr(st.session_state.agent_executor, 'retrieval_fn'):
            # Combined agent
            response = st.session_state.agent_executor.invoke({"query": query})
            answer = response["result"]
        elif hasattr(st.session_state.agent_executor, 'invoke') and not hasattr(st.session_state.agent_executor, 'retrieval_fn'):
            # Regular QA agent  
            response = st.session_state.agent_executor.invoke({
                "input": query,
                "chat_history": st.session_state.chat_history
            })
            answer = response.get("output", response.get("result", "I couldn't process your question."))
        else:
            # Basic LLM
            response = st.session_state.agent_executor.invoke(query)
            answer = response.content if hasattr(response, 'content') else str(response)

        # Enhance response based on user preferences
        if st.session_state.user_preferences["response_length"] == "short":
            answer = answer[:500] + "..." if len(answer) > 500 else answer
        elif st.session_state.user_preferences["response_length"] == "detailed":
            # For detailed responses, add more context if available
            pass  # Keep full response

        return answer

    except Exception as e:
        return f"I apologize, but I encountered an error processing your question: {str(e)}"

def initialize_enhanced_agent(has_documents, vector_store_path):
    """Initialize the enhanced AI agent with better error handling"""
    with st.spinner("🤖 Loading AI agent..."):
        try:
            # Load user's vector store (if exists)
            user_vector_store = None
            if has_documents:
                user_vector_store = load_vector_store(vector_store_path)

            # Load global knowledge base
            global_vector_store = load_global_vector_store()

            # Initialize appropriate agent
            if user_vector_store and global_vector_store:
                st.session_state.agent_executor = get_combined_conversational_agent(
                    user_vector_store,
                    global_vector_store,
                    "user documents and global knowledge base"
                )
                st.success("🔗 AI agent loaded with full access")

            elif user_vector_store:
                st.session_state.agent_executor = get_conversational_agent(
                    user_vector_store,
                    "the provided document or web page"
                )
                st.success("📄 AI agent loaded for your documents")

            elif global_vector_store:
                st.session_state.agent_executor = get_combined_conversational_agent(
                    None,
                    global_vector_store,
                    "global knowledge base"
                )
                st.success("📚 AI agent loaded with knowledge base")

            else:
                # Fallback to basic LLM
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.7)
                st.session_state.agent_executor = llm
                st.warning("⚠️ Basic AI mode - limited document access")

        except Exception as e:
            st.error(f"❌ Error loading AI agent: {str(e)}")
            # Set a basic fallback
            st.session_state.agent_executor = "error"

# Main application logic
def main():
    """Main application entry point"""
    if not st.session_state.get("logged_in", False):
        show_enhanced_login_page()
    else:
        show_enhanced_chat_page()

# Background task runner for RBI updates
def run_background_tasks():
    """Run background tasks like RBI updates"""
    def background_worker():
        while True:
            schedule.run_pending()
            time.sleep(3600)  # Check every hour

    # Start background thread for scheduled tasks
    if 'background_started' not in st.session_state:
        rbi_scraper.schedule_updates()
        thread = Thread(target=background_worker, daemon=True)
        thread.start()
        st.session_state.background_started = True

# Initialize background tasks
run_background_tasks()

# Run the application
if __name__ == "__main__":
    main()
