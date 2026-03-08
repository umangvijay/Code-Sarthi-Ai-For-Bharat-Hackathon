# Code-Sarthi Requirements Document

## Project Overview

**Project Name:** Code-Sarthi - Hinglish Code Assistant  
**Target Users:** Indian engineering students  
**Primary Goal:** Bridge the language gap in programming education by providing AI-powered code explanations and translations in natural Hinglish (Hindi-English mix)

---

## 1. Core Features

### 1.1 Code Explanation
**Requirement ID:** REQ-1.1  
**Priority:** High  
**Description:** Provide instant Hinglish explanations for code snippets in any programming language

**Acceptance Criteria:**
- Accept code input via text area (minimum 300 lines capacity)
- Detect programming language automatically (Python, Java, C++, JavaScript)
- Generate explanations using AWS Bedrock (Claude 3.5 Sonnet)
- Preserve technical terms in English (function, variable, loop, etc.)
- Use natural Hindi for general explanations (samajhna, karna, hona)
- Display output in read-only formatted container
- Response time: < 5 seconds for typical code snippets
- Track usage in conversation history

### 1.2 Text Translation
**Requirement ID:** REQ-1.2  
**Priority:** High  
**Description:** Convert technical English content to natural Hinglish while maintaining accuracy

**Acceptance Criteria:**
- Accept English text input (minimum 200 lines capacity)
- Translate using AWS Bedrock with custom prompts
- Preserve programming keywords and technical terms
- Use natural code-switching patterns
- Display translated output in formatted container
- Cache translations using LRU cache (128 entries)
- Response time: < 3 seconds for typical text
- Track translation count in session state

### 1.3 PDF Upload & Processing
**Requirement ID:** REQ-1.3  
**Priority:** Medium  
**Description:** Extract and process text from PDF lab manuals and documentation

**Acceptance Criteria:**
- Accept PDF file uploads (single file, max 10MB)
- Extract text using PyPDF2
- Display extraction statistics (characters, words, chunks)
- Chunk text into 500-1000 token segments using tiktoken
- Show chunk analysis and preview
- Provide download option for extracted text
- Store document metadata in session state
- Handle extraction errors gracefully

### 1.4 Voice Viva Practice
**Requirement ID:** REQ-1.4  
**Priority:** High  
**Description:** AI-powered interview practice with real-time evaluation

**Acceptance Criteria:**
- Provide sample questions across 4 topics (Python, Data Structures, OOP, Web Dev)
- Accept text-based answers in English, Hindi, or Hinglish
- Evaluate answers using AWS Bedrock with 3D scoring:
  - Correctness (0.0-1.0)
  - Completeness (0.0-1.0)
  - Clarity (0.0-1.0)
  - Overall score (weighted average)
- Generate natural Hinglish feedback
- Create intelligent follow-up questions based on performance
- Track viva history and statistics
- Display strengths and improvement areas
- Response time: < 3 seconds for evaluation

### 1.5 Personalized Learning Path
**Requirement ID:** REQ-1.5  
**Priority:** High  
**Description:** Generate AI-powered personalized study plans based on user history

**Acceptance Criteria:**
- Analyze conversation history (code explanations, translations, viva sessions)
- Extract topics studied from user interactions
- Generate 7-day personalized study plan using AWS Bedrock
- Include analysis of strong/weak areas
- Provide focus areas and practice recommendations
- Display learning statistics (total interactions, by type)
- Show recent topics studied
- Provide download option for study plan (JSON format)
- Motivational content in natural Hinglish

---

## 2. User Interface Requirements

### 2.1 Theme System
**Requirement ID:** REQ-2.1  
**Priority:** High  
**Description:** Responsive theme system with Light/Dark/System modes

**Acceptance Criteria:**
- Support three theme modes: Light, Dark, System
- Light theme: #FFFFFF cards, #1E1E1E text, #F8F9FA sidebar
- Dark theme: #1C1C1E cards, #E0E0E0 text, #161616 sidebar
- Orange accent color: #FF8A00 (vibrant in both themes)
- System theme: Auto-detect OS preference using JavaScript
- Theme persistence across page navigation
- Smooth transitions (300ms ease-in-out)
- All UI elements respect theme (cards, text, borders, shadows)
- Use !important tags to override Streamlit defaults

### 2.2 Navigation & Layout
**Requirement ID:** REQ-2.2  
**Priority:** High  
**Description:** Multi-page structure with intuitive navigation

**Acceptance Criteria:**
- Home page with feature cards
- 7 pages: Code Explanation, Text Translation, PDF Upload, Voice Viva, Learning Path, AWS Status, About
- Sidebar navigation with icons
- Responsive layout (wide mode)
- Feature cards with hover effects (translateY, shadow)
- Statistics display in sidebar (translations, PDFs)
- Mode indicator (AWS Cloud / Local Offline)
- Clean branding (hidden Streamlit menu/footer)

### 2.3 Interactive Elements
**Requirement ID:** REQ-2.3  
**Priority:** Medium  
**Description:** Professional UI components with animations

**Acceptance Criteria:**
- Gradient buttons with hover effects
- Animated feature cards (fade-in-up on load)
- Status boxes (success, error, info) with color coding
- Metric cards with hover scale effect
- Read-only output containers with proper styling
- Loading spinners for async operations
- Download buttons for exports
- Proper spacing and padding throughout

---

## 3. AWS Integration Requirements

### 3.1 Amazon Bedrock
**Requirement ID:** REQ-3.1  
**Priority:** Critical  
**Description:** Core AI functionality using Claude 3.5 Sonnet

**Acceptance Criteria:**
- Model: anthropic.claude-3-5-sonnet-20241022-v2:0
- Authentication: IAM roles via boto3.Session() (no hardcoded credentials)
- Region: us-east-1 (configurable)
- Retry logic: 3 attempts with exponential backoff (2s, 4s, 8s)
- Error handling: Graceful fallback with user-friendly messages
- Temperature: 0.5 for translations, 0.7 for explanations, 0.3 for evaluations
- Max tokens: 2000-3000 depending on use case
- Real-time dynamic invocation (no hardcoded responses)

### 3.2 Hybrid Mode Architecture
**Requirement ID:** REQ-3.2  
**Priority:** High  
**Description:** Support both AWS Cloud and Local Offline modes

**Acceptance Criteria:**
- Environment variable control: USE_AWS=True/False
- AWS mode: Full Bedrock integration
- Local mode: Mock responses with clear indicators (🔵 Local Mode)
- Graceful service checks on startup
- Mode display in sidebar
- No crashes when AWS unavailable
- Clear setup instructions for AWS configuration

### 3.3 AWS Kendra (Optional)
**Requirement ID:** REQ-3.3  
**Priority:** Low  
**Description:** Semantic search for PDF content

**Acceptance Criteria:**
- Configuration via kendra_config.json
- Optional enablement (kendra_enabled: true/false)
- Index ID externalized (no hardcoding)
- Graceful fallback to local metadata storage
- Batch indexing (10 documents per batch)
- Relevance threshold: 0.7
- Top K results: 5
- Clear setup instructions in config file

---

## 4. Performance Requirements

### 4.1 Response Times
**Requirement ID:** REQ-4.1  
**Priority:** High  
**Description:** Fast response times for all operations

**Acceptance Criteria:**
- Code explanation: < 5 seconds
- Text translation: < 3 seconds
- Viva evaluation: < 3 seconds
- PDF extraction: < 10 seconds for typical PDFs
- Learning path generation: < 8 seconds
- Page navigation: < 1 second
- Theme switching: < 500ms

### 4.2 Cost Optimization
**Requirement ID:** REQ-4.2  
**Priority:** High  
**Description:** Minimize AWS API costs through intelligent caching and heuristics

**Acceptance Criteria:**
- LRU cache for translations (128 entries, 40% cost reduction)
- RAG heuristics to avoid unnecessary Kendra queries (60% cost reduction)
- Retry logic to prevent wasted failed calls
- Efficient token counting using tiktoken
- Batch operations where possible
- Smart chunking to optimize context windows

### 4.3 Scalability
**Requirement ID:** REQ-4.3  
**Priority:** Medium  
**Description:** Support multiple concurrent users

**Acceptance Criteria:**
- Stateless architecture (session state per user)
- No shared mutable state between users
- Efficient memory usage
- Support for EC2 deployment with auto-scaling
- Load balancer compatible

---

## 5. Security Requirements

### 5.1 Credential Management
**Requirement ID:** REQ-5.1  
**Priority:** Critical  
**Description:** Secure handling of AWS credentials

**Acceptance Criteria:**
- IAM role authentication (no hardcoded keys)
- Environment variable for sensitive config
- Comprehensive .gitignore (excludes .env, *.pem, credentials)
- No credentials in code or logs
- boto3.Session() for automatic credential discovery

### 5.2 Data Privacy
**Requirement ID:** REQ-5.2  
**Priority:** High  
**Description:** Protect user data and conversation history

**Acceptance Criteria:**
- Session-based storage (no persistent user data)
- Conversation history stored in session state only
- No logging of sensitive information
- PDF metadata stored locally (excluded from git)
- Export functionality for user data portability

---

## 6. Monitoring & Analytics

### 6.1 Usage Tracking
**Requirement ID:** REQ-6.1  
**Priority:** Medium  
**Description:** Track application usage and performance

**Acceptance Criteria:**
- Track API calls by service (Bedrock, Kendra, S3)
- Track response times by operation type
- Count translations and PDF uploads
- Store conversation history in session
- Display statistics in sidebar
- Analytics module for aggregation

### 6.2 Error Logging
**Requirement ID:** REQ-6.2  
**Priority:** Medium  
**Description:** Log errors for debugging and monitoring

**Acceptance Criteria:**
- Log AWS service errors
- Log PDF extraction failures
- Log evaluation errors
- User-friendly error messages in UI
- Technical details in console/logs

---

## 7. Deployment Requirements

### 7.1 EC2 Deployment
**Requirement ID:** REQ-7.1  
**Priority:** High  
**Description:** Production deployment on AWS EC2

**Acceptance Criteria:**
- Automated deployment script (deploy.sh)
- Ubuntu compatibility
- Python 3.8+ support
- Virtual environment setup
- Systemd service or tmux for persistence
- Port 8501 exposed
- IAM instance profile for AWS access

### 7.2 Dependencies
**Requirement ID:** REQ-7.2  
**Priority:** Critical  
**Description:** All required packages documented and installable

**Acceptance Criteria:**
- requirements.txt with pinned versions
- Core: streamlit>=1.31.0, boto3>=1.34.0
- AI: tiktoken>=0.5.0, tenacity>=8.2.0
- PDF: PyPDF2>=3.0.0
- UI: streamlit-option-menu>=0.3.6
- All dependencies installable via pip

---

## 8. Documentation Requirements

### 8.1 User Documentation
**Requirement ID:** REQ-8.1  
**Priority:** Medium  
**Description:** Clear documentation for users and developers

**Acceptance Criteria:**
- README.md with setup instructions
- Architecture documentation
- Deployment guide
- Kendra configuration guide
- Troubleshooting section

### 8.2 Code Documentation
**Requirement ID:** REQ-8.2  
**Priority:** Medium  
**Description:** Well-documented codebase

**Acceptance Criteria:**
- Docstrings for all classes and functions
- Type hints for function parameters
- Inline comments for complex logic
- Module-level documentation
- Requirements traceability in code comments

---

## 9. Quality Requirements

### 9.1 Code Quality
**Requirement ID:** REQ-9.1  
**Priority:** High  
**Description:** Production-ready code quality

**Acceptance Criteria:**
- No syntax errors or linting issues
- Proper error handling throughout
- Consistent code style
- Modular architecture (separation of concerns)
- Reusable components
- Type safety where applicable

### 9.2 Reliability
**Requirement ID:** REQ-9.2  
**Priority:** High  
**Description:** Stable and reliable operation

**Acceptance Criteria:**
- Graceful degradation when services unavailable
- No crashes on invalid input
- Retry logic for transient failures
- Clear error messages for users
- Fallback mechanisms for critical features

---

## 10. Accessibility Requirements

### 10.1 Language Support
**Requirement ID:** REQ-10.1  
**Priority:** High  
**Description:** Natural Hinglish support

**Acceptance Criteria:**
- Accept input in English, Hindi, or Hinglish
- Generate output in natural Hinglish
- Preserve technical terms in English
- Use Roman script for Hindi words (not Devanagari)
- Natural code-switching patterns

### 10.2 User Experience
**Requirement ID:** REQ-10.2  
**Priority:** High  
**Description:** Intuitive and accessible interface

**Acceptance Criteria:**
- Clear navigation
- Helpful placeholder text
- Tooltips for guidance
- Loading indicators for async operations
- Success/error feedback
- Responsive design

---

## Non-Functional Requirements

### NFR-1: Maintainability
- Modular code structure
- Clear separation of concerns
- Consistent naming conventions
- Version control (Git)

### NFR-2: Extensibility
- Easy to add new features
- Pluggable architecture
- Configuration-driven behavior
- Support for new AWS services

### NFR-3: Testability
- Unit testable components
- Mock-friendly architecture
- Test data generation support
- Local testing without AWS

---

## Success Metrics

1. **User Engagement:** Average session duration > 10 minutes
2. **Feature Adoption:** All 5 core features used regularly
3. **Performance:** 95% of operations complete within target times
4. **Cost Efficiency:** API costs < $5/user/month
5. **Reliability:** 99% uptime, < 1% error rate
6. **User Satisfaction:** Positive feedback on Hinglish quality

---

## Future Enhancements (Out of Scope)

- Voice input/output for viva practice
- Multi-user collaboration features
- Advanced analytics dashboard
- Mobile app version
- Integration with learning management systems
- Support for more programming languages
- Video tutorial generation
- Code debugging assistance
