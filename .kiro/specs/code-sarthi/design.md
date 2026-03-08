# Code-Sarthi Design Document

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     User Browser                             │
│                   (Streamlit Frontend)                       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Streamlit Application                       │
│                      (app.py)                                │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Session State Manager                                │  │
│  │  - Theme Manager                                      │  │
│  │  - Translation Engine                                 │  │
│  │  - AWS Config                                         │  │
│  │  - Conversation History                               │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
        ▼              ▼              ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Pages/     │ │   Utils/     │ │   AWS        │
│   Modules    │ │   Modules    │ │   Modules    │
└──────────────┘ └──────────────┘ └──────────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │      AWS Services            │
        │  ┌────────────────────────┐  │
        │  │  Amazon Bedrock        │  │
        │  │  (Claude 3.5 Sonnet)   │  │
        │  └────────────────────────┘  │
        │  ┌────────────────────────┐  │
        │  │  Amazon Kendra         │  │
        │  │  (Optional)            │  │
        │  └────────────────────────┘  │
        │  ┌────────────────────────┐  │
        │  │  Amazon S3             │  │
        │  │  (Optional)            │  │
        │  └────────────────────────┘  │
        └──────────────────────────────┘
```

### 1.2 Component Architecture

```
code-sarthi/
├── app.py                          # Main entry point
├── pages/                          # Multi-page modules
│   ├── 1_💡_Code_Explanation.py
│   ├── 2_🌐_Text_Translation.py
│   ├── 3_📚_PDF_Upload.py
│   ├── 4_🎤_Voice_Viva.py
│   ├── 5_🎯_Learning_Path.py
│   ├── 6_☁️_AWS_Status.py
│   └── 7_ℹ️_About.py
├── utils/                          # Utility modules
│   └── theme_manager.py
├── aws_config.py                   # AWS configuration
├── aws_bedrock_utils.py            # Bedrock client
├── translation_engine.py           # Translation logic
├── rag_engine.py                   # RAG pipeline
├── aws_viva_evaluation.py          # Viva evaluation
├── monitoring_analytics.py         # Analytics tracking
└── kendra_config.json              # Kendra configuration
```

---

## 2. Core Components Design

### 2.1 Main Application (app.py)

**Purpose:** Entry point, session state management, routing

**Key Functions:**
- `initialize_session_state()`: Initialize all session variables
- `check_aws_services()`: Validate AWS connectivity
- `render_sidebar()`: Display navigation and statistics
- `home_page()`: Render landing page with feature cards
- `main()`: Application entry point

**Session State Variables:**
```python
{
    "theme_mode": str,              # "light" | "dark" | "system"
    "theme_manager": ThemeManager,
    "translation_engine": TranslationEngine,
    "aws_config": AWSConfig,
    "services_checked": bool,
    "translation_count": int,
    "pdf_count": int,
    "conversation_history": list,
    "analytics": Analytics,
    "pdf_documents": list,
    "rag_engine": RAGEngine,
    "viva_history": list
}
```

**Design Decisions:**
- Centralized session state for data sharing across pages
- Lazy initialization of AWS clients (only when needed)
- Theme manager injected on every page load
- Analytics tracking for all user interactions

---

### 2.2 Theme Manager (utils/theme_manager.py)

**Purpose:** Manage application themes and CSS injection

**Class: ThemeManager**

**Attributes:**
```python
THEME_COLORS = {
    'light': {
        'background': '#FFFFFF',
        'sidebar': '#F8F9FA',
        'text': '#1E1E1E',
        'text_secondary': '#666666',
        'border': '#E0E0E0',
        'card_bg': '#FFFFFF',
        'card_shadow': 'rgba(0, 0, 0, 0.1)',
        'hover_shadow': 'rgba(255, 138, 0, 0.2)',
        'gradient_bg': 'linear-gradient(135deg, #F8F9FA 0%, #FFFFFF 100%)',
        'sidebar_gradient': 'linear-gradient(180deg, #F8F9FA 0%, #FFFFFF 100%)'
    },
    'dark': {
        'background': '#0F0F0F',
        'sidebar': '#161616',
        'text': '#E0E0E0',
        'text_secondary': '#A0A0A0',
        'border': '#2A2A2A',
        'card_bg': '#1C1C1E',
        'card_shadow': 'rgba(0, 0, 0, 0.3)',
        'hover_shadow': 'rgba(255, 138, 0, 0.4)',
        'gradient_bg': 'linear-gradient(135deg, #0F0F0F 0%, #1A1A1A 100%)',
        'sidebar_gradient': 'linear-gradient(180deg, #161616 0%, #0F0F0F 100%)'
    },
    'accent': {
        'primary': '#FF8A00',
        'secondary': '#FF5E00',
        'gradient': 'linear-gradient(135deg, #FF8A00 0%, #FF5E00 100%)'
    }
}
```

**Methods:**
- `detect_system_theme()`: Use JavaScript to detect OS theme preference
- `get_current_theme()`: Determine active theme based on mode
- `inject_theme_css()`: Inject CSS with !important tags
- `render_theme_toggle()`: Display theme selector in sidebar

**Design Decisions:**
- Use !important tags to override Streamlit defaults
- JavaScript-based system theme detection
- Smooth transitions (300ms ease-in-out)
- Theme persistence in session state

---

### 2.3 Translation Engine (translation_engine.py)

**Purpose:** Convert English to Hinglish using AWS Bedrock

**Class: TranslationEngine**

**Attributes:**
```python
TECHNICAL_TERMS = {
    'if', 'else', 'for', 'while', 'function', 'class',
    'variable', 'array', 'loop', 'return', ...
}
```

**Methods:**
- `translate(text, preserve_terms)`: Main translation method
- `detect_technical_terms(text)`: Identify terms to preserve
- `apply_translation_rules(text, terms)`: Call Bedrock with retry logic
- `_build_translation_prompt(text, terms)`: Construct prompt
- `_generate_cache_key(text)`: Generate MD5 hash for caching
- `_get_from_cache(cache_key)`: LRU cache lookup
- `_store_in_cache(cache_key, translation)`: Cache storage

**Design Decisions:**
- LRU cache with 128 entries (40% cost reduction)
- Retry logic: 3 attempts with exponential backoff (2s, 4s, 8s)
- Temperature: 0.5 for consistent translations
- Preserve technical terms using regex patterns
- Hybrid mode support (USE_AWS environment variable)

**Translation Prompt Structure:**
```
You are a translation expert for Code-Sarthi...

CRITICAL TRANSLATION RULES:
1. Translate general concepts to common Hindi words
2. Keep ALL programming keywords in English
3. Use natural code-switching patterns
4. Preserve code blocks exactly
5. Use Roman script for Hindi

TEXT TO TRANSLATE: {text}
TECHNICAL TERMS TO PRESERVE: {terms}
```

---

### 2.4 RAG Engine (rag_engine.py)

**Purpose:** Document chunking, indexing, and retrieval

**Class: RAGEngine**

**Methods:**
- `chunk_text(text, chunk_size, overlap)`: Split into 500-1000 token chunks
- `index_document(doc_id, name, text, user_id, callback)`: Index in Kendra
- `retrieve(query, top_k, threshold)`: Semantic search
- `should_use_rag(query)`: Heuristic to avoid unnecessary queries
- `_split_into_sentences(text)`: Sentence boundary detection
- `_count_tokens(text)`: Accurate counting with tiktoken
- `_load_kendra_config()`: Read kendra_config.json

**Design Decisions:**
- Tiktoken for accurate token counting (cl100k_base encoding)
- Sentence boundary preservation in chunks
- 100-token overlap between chunks
- Minimum chunk size: 500 tokens
- Maximum chunk size: 1000 tokens
- RAG heuristics: 60% cost reduction
- Graceful fallback to local metadata storage

**Chunking Algorithm:**
```python
1. Split text into sentences
2. Accumulate sentences until target size (800 tokens)
3. If exceeds max (1000), save chunk
4. Start new chunk with overlap (100 tokens)
5. Repeat until all text processed
6. Discard final chunk if < 500 tokens
```

**RAG Heuristics:**
```python
Keywords: ['lab', 'assignment', 'manual', 'explain', 'documentation']
- If query contains keyword → Use RAG
- If query < 5 words → Skip RAG
- If query contains code → Skip RAG (unless > 10 words)
- If query >= 10 words → Use RAG
```

---

### 2.5 Viva Evaluation (aws_viva_evaluation.py)

**Purpose:** Evaluate student answers with 3D scoring

**Class: VivaAnswerEvaluator**

**Methods:**
- `evaluate_answer(question, answer, expected_concepts, context)`: Main evaluation
- `_build_evaluation_prompt(...)`: Construct evaluation prompt
- `_parse_evaluation_response(text)`: Parse JSON response

**Evaluation Dimensions:**
1. **Correctness (0.0-1.0):** Technical accuracy
2. **Completeness (0.0-1.0):** Coverage of key concepts
3. **Clarity (0.0-1.0):** Explanation quality

**Overall Score Calculation:**
```python
overall = (correctness * 0.4) + (completeness * 0.35) + (clarity * 0.25)
```

**Response Format:**
```json
{
  "correctness_score": 0.8,
  "completeness_score": 0.7,
  "clarity_score": 0.9,
  "feedback": "Tumhara answer sahi direction mein hai!...",
  "follow_up_question": "Achha, ab yeh batao...",
  "strengths": ["Good understanding of basics"],
  "improvements": ["Add more details about parameters"]
}
```

**Design Decisions:**
- Temperature: 0.3 for consistent evaluation
- JSON-structured response for parsing
- Weighted scoring (correctness most important)
- Dynamic follow-up questions based on performance
- Natural Hinglish feedback

---

### 2.6 AWS Configuration (aws_config.py)

**Purpose:** Manage AWS credentials and service checks

**Class: AWSConfig**

**Methods:**
- `validate_credentials()`: Check IAM role/credentials
- `check_bedrock_access()`: Verify Bedrock availability
- `check_s3_access()`: Verify S3 availability
- `check_kendra_access()`: Verify Kendra availability (optional)
- `check_all_services()`: Run all checks
- `get_service_status_summary()`: Status string
- `is_local_mode()`: Check if USE_AWS=False
- `get_mode_display()`: Display string for UI

**Design Decisions:**
- IAM role authentication via boto3.Session()
- Hybrid mode support (USE_AWS environment variable)
- Graceful degradation when services unavailable
- Clear error messages with setup instructions
- Optional services (Kendra, S3) don't block startup

---

## 3. Page Designs

### 3.1 Code Explanation Page

**File:** `pages/1_💡_Code_Explanation.py`

**UI Components:**
- Text area for code input (300 lines)
- "How it works" info card
- "Explain in Hinglish" button
- Output container with formatted explanation

**Flow:**
```
1. User pastes code
2. Click "Explain in Hinglish"
3. Validate input (not empty)
4. Check translation engine ready
5. Show spinner
6. Call translation_engine.translate()
7. Track analytics
8. Increment translation_count
9. Record in conversation_history
10. Display formatted output
```

---

### 3.2 Text Translation Page

**File:** `pages/2_🌐_Text_Translation.py`

**UI Components:**
- Text area for English input (200 lines)
- "Translate to Hinglish" button
- Output container with translated text

**Flow:**
```
1. User enters English text
2. Click "Translate to Hinglish"
3. Validate input
4. Check translation engine ready
5. Show spinner
6. Call translation_engine.translate()
7. Track analytics
8. Increment translation_count
9. Record in conversation_history
10. Display translated output
```

---

### 3.3 PDF Upload Page

**File:** `pages/3_📚_PDF_Upload.py`

**UI Components:**
- File uploader (single PDF)
- "Extract & Analyze Text" button
- Statistics cards (characters, words, chunks)
- Text preview container
- Chunk analysis expander
- Download button for extracted text

**Flow:**
```
1. User uploads PDF
2. Click "Extract & Analyze Text"
3. Extract text using PyPDF2
4. Chunk text using RAG engine
5. Store in pdf_documents
6. Increment pdf_count
7. Display statistics
8. Show text preview (first 2000 chars)
9. Show chunk details (first 3 chunks)
10. Provide download option
```

---

### 3.4 Voice Viva Page

**File:** `pages/4_🎤_Voice_Viva.py`

**UI Components:**
- Topic selector (4 topics)
- Question selector
- Random question button
- Answer text area
- Submit button
- Score cards (4 metrics)
- Feedback container
- Strengths/improvements columns
- Follow-up question card
- Statistics display (attempts, avg score)

**Flow:**
```
1. User selects topic
2. User selects or randomizes question
3. User types answer in Hinglish
4. Click "Submit Answer for Evaluation"
5. Validate input
6. Check AWS config ready
7. Show spinner
8. Call VivaAnswerEvaluator.evaluate_answer()
9. Track analytics
10. Store in viva_history
11. Display scores (overall, correctness, completeness, clarity)
12. Display Hinglish feedback
13. Show strengths and improvements
14. Display follow-up question
15. Option to answer follow-up
```

**Sample Questions:**
```python
{
    "Python Basics": [
        "What is a function in Python?",
        "Explain the difference between list and tuple",
        "What is a dictionary and when would you use it?",
        "How does a for loop work in Python?"
    ],
    "Data Structures": [...],
    "OOP Concepts": [...],
    "Web Development": [...]
}
```

---

### 3.5 Learning Path Page

**File:** `pages/5_🎯_Learning_Path.py`

**UI Components:**
- Learning statistics cards (total, code, translations, viva)
- Recent topics display
- "Generate My Personalized Study Plan" button
- Study plan output container
- Download button for plan (JSON)

**Flow:**
```
1. Analyze conversation_history
2. Extract topics from interactions
3. Count interactions by type
4. Display statistics
5. Show recent topics (last 10 interactions)
6. Click "Generate Study Plan"
7. Check translation engine ready
8. Show spinner
9. Build prompt with analysis
10. Call translation_engine.translate()
11. Track analytics
12. Display study plan
13. Provide download option (JSON with metadata)
```

**Analysis Logic:**
```python
def analyze_learning_history():
    - Count total interactions
    - Count by type (code_explanation, translation, viva)
    - Extract topics using keyword matching
    - Return analysis dict
```

**Study Plan Prompt:**
```
You are Code-Sarthi, an AI tutor...

STUDENT LEARNING HISTORY:
- Total interactions: {count}
- Code explanations: {count}
- Translations: {count}
- Viva sessions: {count}
- Recent topics: {topics}

Create a personalized 7-day study plan in Hinglish:
1. Analysis (strong/weak points)
2. Focus Areas
3. 7-Day Plan (day-wise breakdown)
4. Practice Recommendations
5. Motivation
```

---

### 3.6 AWS Status Page

**File:** `pages/6_☁️_AWS_Status.py`

**UI Components:**
- Service status cards (Credentials, Bedrock, S3)
- Detailed status JSON display

**Flow:**
```
1. Check aws_config initialized
2. Call aws_config.check_all_services()
3. Display service cards with icons
4. Show status (Active/Inactive)
5. Display detailed JSON
```

---

### 3.7 About Page

**File:** `pages/7_ℹ️_About.py`

**UI Components:**
- Project description card
- Mission and "Powered By" cards
- Architecture features list

**Content:**
- Project overview
- Mission statement
- Technology stack
- Production-ready features

---

## 4. Data Models

### 4.1 Conversation History Entry
```python
{
    "timestamp": "2024-03-08 14:30:00",
    "type": "code_explanation" | "translation" | "viva",
    "input": str,
    "output": str
}
```

### 4.2 PDF Document Entry
```python
{
    "id": "doc_20240308_143000",
    "name": "lab_manual.pdf",
    "text": str,
    "timestamp": "2024-03-08 14:30:00",
    "size": int  # character count
}
```

### 4.3 Viva History Entry
```python
{
    "question": str,
    "answer": str,
    "score": float,  # overall score
    "timestamp": datetime
}
```

### 4.4 Analytics Data
```python
{
    "api_calls": {
        "bedrock": int,
        "kendra": int,
        "s3": int
    },
    "response_times": {
        "code_explanation": [float],
        "translation": [float],
        "viva_evaluation": [float],
        "pdf_processing": [float],
        "learning_path": [float]
    }
}
```

---

## 5. API Integration Design

### 5.1 AWS Bedrock Integration

**Model:** anthropic.claude-3.5-sonnet-20241022-v2:0

**Request Structure:**
```python
{
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 2000-3000,
    "messages": [
        {
            "role": "user",
            "content": prompt
        }
    ],
    "temperature": 0.3-0.7
}
```

**Response Structure:**
```python
{
    "content": [
        {
            "text": str
        }
    ]
}
```

**Error Handling:**
- ClientError → Retry with exponential backoff
- AccessDeniedException → Show setup instructions
- Other exceptions → Graceful fallback with error message

---

### 5.2 AWS Kendra Integration (Optional)

**Operations:**
- `batch_put_document()`: Index chunks (10 per batch)
- `query()`: Semantic search

**Document Structure:**
```python
{
    "Id": "doc_id_chunk_id",
    "Title": "Document Name - Chunk N",
    "Blob": bytes,
    "ContentType": "PLAIN_TEXT",
    "Attributes": [
        {"Key": "_source_uri", "Value": {"StringValue": doc_id}},
        {"Key": "chunk_index", "Value": {"LongValue": index}}
    ]
}
```

**Query Parameters:**
```python
{
    "IndexId": str,
    "QueryText": str,
    "PageSize": 5
}
```

---

## 6. Security Design

### 6.1 Authentication & Authorization
- IAM role-based authentication (no hardcoded credentials)
- boto3.Session() for automatic credential discovery
- Environment variable for mode control (USE_AWS)

### 6.2 Data Protection
- Session-based storage (no persistent user data)
- No logging of sensitive information
- .gitignore excludes credentials and keys
- PDF metadata stored locally (not in git)

### 6.3 Input Validation
- Text length limits on inputs
- File type validation (PDF only)
- File size limits (10MB)
- Sanitization of user inputs before API calls

---

## 7. Performance Design

### 7.1 Caching Strategy
- LRU cache for translations (128 entries)
- Cache key: MD5 hash of input text
- Cache hit rate target: 40%

### 7.2 Optimization Techniques
- Lazy initialization of AWS clients
- Batch operations for Kendra indexing
- Efficient token counting with tiktoken
- RAG heuristics to avoid unnecessary queries
- Retry logic to prevent wasted calls

### 7.3 Response Time Targets
- Code explanation: < 5s
- Translation: < 3s
- Viva evaluation: < 3s
- PDF extraction: < 10s
- Page navigation: < 1s

---

## 8. Error Handling Design

### 8.1 Error Categories
1. **AWS Service Errors:** Bedrock, Kendra, S3 failures
2. **Input Validation Errors:** Empty input, invalid format
3. **Processing Errors:** PDF extraction, text chunking
4. **Network Errors:** Timeout, connection issues

### 8.2 Error Handling Strategy
- Try-except blocks around all AWS calls
- Retry logic for transient failures (3 attempts)
- Graceful degradation (local mode fallback)
- User-friendly error messages in UI
- Technical details in console logs

### 8.3 Error Message Design
```python
# User-facing (Hinglish)
"Translation engine ready nahi hai. AWS Status page check karein."

# Technical (console)
"BedrockClient initialization failed: AccessDeniedException"
```

---

## 9. Deployment Design

### 9.1 EC2 Deployment Architecture
```
┌─────────────────────────────────────┐
│         AWS EC2 Instance            │
│  ┌──────────────────────────────┐  │
│  │  Ubuntu 20.04/22.04          │  │
│  │  ┌────────────────────────┐  │  │
│  │  │  Python 3.8+           │  │  │
│  │  │  Virtual Environment   │  │  │
│  │  │  ┌──────────────────┐  │  │  │
│  │  │  │  Streamlit App   │  │  │  │
│  │  │  │  (Port 8501)     │  │  │  │
│  │  │  └──────────────────┘  │  │  │
│  │  └────────────────────────┘  │  │
│  └──────────────────────────────┘  │
│  IAM Instance Profile               │
│  (Bedrock, Kendra, S3 permissions)  │
└─────────────────────────────────────┘
```

### 9.2 Deployment Script (deploy.sh)
```bash
1. Update system packages
2. Install Python 3 and pip
3. Clone repository
4. Create virtual environment
5. Install requirements
6. Set environment variables
7. Start Streamlit in tmux
8. Expose port 8501
```

---

## 10. Testing Strategy

### 10.1 Unit Testing
- Test individual functions in isolation
- Mock AWS services for testing
- Test caching logic
- Test chunking algorithm
- Test theme switching

### 10.2 Integration Testing
- Test AWS service integration
- Test page navigation
- Test session state persistence
- Test error handling flows

### 10.3 User Acceptance Testing
- Test all features end-to-end
- Verify Hinglish quality
- Test theme switching
- Verify response times
- Test error scenarios

---

## 11. Monitoring & Observability

### 11.1 Metrics to Track
- API call counts by service
- Response times by operation
- Error rates by type
- Cache hit rates
- User engagement (session duration, feature usage)

### 11.2 Logging Strategy
- Console logs for development
- File logs for production (optional)
- Error logs with stack traces
- AWS CloudWatch integration (optional)

---

## 12. Future Enhancements

### 12.1 Phase 2 Features
- Voice input/output for viva
- Real-time collaboration
- Advanced analytics dashboard
- Mobile app version

### 12.2 Technical Improvements
- WebSocket for real-time updates
- Database for persistent storage
- User authentication
- Multi-language support
- Advanced caching (Redis)

---

## Design Principles

1. **Modularity:** Separate concerns, reusable components
2. **Scalability:** Stateless architecture, horizontal scaling
3. **Reliability:** Retry logic, graceful degradation
4. **Security:** IAM roles, no hardcoded credentials
5. **Performance:** Caching, optimization, efficient algorithms
6. **Usability:** Intuitive UI, clear feedback, helpful errors
7. **Maintainability:** Clean code, documentation, type hints
8. **Extensibility:** Plugin architecture, configuration-driven
