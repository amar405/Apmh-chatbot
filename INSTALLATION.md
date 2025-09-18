# APMH Enhanced ChatBot Installation Guide

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Download SpaCy Language Model (Optional)
```bash
python -m spacy download en_core_web_sm
```

### 3. Set up Environment Variables
Create a `.env` file with:
```
GOOGLE_API_KEY=your_gemini_api_key_here
```

### 4. Create Required Directories
```bash
mkdir -p user_data
mkdir -p preloaded_docs
mkdir -p scraped_data/RBI
mkdir -p global_knowledge_base
```

### 5. Run the Application
```bash
streamlit run enhanced_main.py
```

## 📋 Features Overview

### 🔍 Enhanced Search
- **Fuzzy Search**: Finds content even with spelling mistakes
- **Spell Correction**: Automatically corrects common typos
- **Semantic Matching**: Uses AI to understand query intent
- **Adjustable Sensitivity**: Customize search precision

### 📊 Document Analytics
- **Reading Time**: Estimates time needed to read document
- **Keyword Extraction**: Identifies important terms
- **Readability Score**: Measures text difficulty
- **Content Classification**: Categorizes document type

### 🏦 RBI Integration
- **Automated Scraping**: Scheduled updates from RBI website
- **Real-time Monitoring**: Checks for new press releases
- **Change Detection**: Identifies updated content
- **One-click Updates**: Manual refresh capability

### 🎨 Enhanced UI/UX
- **Modern Design**: Gradient styling and clean layout
- **Progress Tracking**: Visual feedback for long operations
- **Error Handling**: Graceful error messages and recovery
- **Responsive Design**: Works on different screen sizes

### ⚙️ Advanced Settings
- **User Preferences**: Customizable response length and style
- **Search History**: Track and reuse previous queries
- **Document Management**: Easy upload, view, and delete
- **Chat Management**: Organize conversations efficiently

## 🛠️ Troubleshooting

### Common Issues

**1. FAISS Index Errors**
- Ensure documents are uploaded correctly
- Try rebuilding the index
- Check file permissions

**2. RBI Scraping Issues**
- Verify internet connection
- Check if RBI website structure changed
- Use manual update button

**3. Memory Issues with Large Documents**
- Split large PDFs into smaller chunks
- Increase system memory if possible
- Use text files instead of complex formats

**4. Slow Performance**
- Reduce fuzzy search sensitivity
- Clear chat history regularly
- Restart the application

### Performance Optimization

**For Better Speed:**
- Use SSD storage for index files
- Increase RAM allocation
- Use GPU for embeddings (if available)

**For Accuracy:**
- Use higher fuzzy search thresholds
- Enable spell correction
- Provide clear, specific queries

## 📚 Usage Tips

### Best Practices

**Document Upload:**
- Use high-quality PDF scans
- Ensure text is selectable in PDFs
- Break large documents into chapters

**Query Formulation:**
- Be specific about what you want
- Use keywords from the document
- Try different phrasings if needed

**Chat Management:**
- Create separate chats for different topics
- Use descriptive chat titles
- Delete old chats to save space

### Example Queries

**Document Analysis:**
- "What are the main points in this document?"
- "Summarize the financial regulations mentioned"
- "Find all mentions of credit policies"
- "Explain the RBI guidelines in simple terms"

**Specific Information:**
- "What is the interest rate mentioned?"
- "List all the compliance requirements"
- "Find the effective date of this circular"
- "Extract all numerical data"

## 🔧 Advanced Configuration

### Custom Settings
Edit the configuration variables in `enhanced_main.py`:
- `FUZZY_SEARCH_THRESHOLD`: Default search sensitivity
- `AUTO_SPELL_CORRECT`: Enable/disable spell correction
- `RBI_UPDATE_INTERVAL`: Hours between automatic updates
- `MAX_CHAT_HISTORY`: Maximum stored conversations

### Integration Options
- Connect to external APIs
- Add custom document processors
- Implement additional scrapers
- Integrate with databases

## 📞 Support

For issues or questions:
1. Check the troubleshooting section
2. Review error messages carefully  
3. Try restarting the application
4. Check system requirements

## 🔄 Updates

To update the application:
1. Pull latest code changes
2. Update dependencies: `pip install -r requirements.txt --upgrade`
3. Restart the application
4. Clear cache if needed

---

**Version**: Enhanced v2.0  
**Last Updated**: September 2025
