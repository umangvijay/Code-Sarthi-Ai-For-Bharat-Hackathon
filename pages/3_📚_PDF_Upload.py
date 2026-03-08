"""
PDF Upload Page
Upload and process lab manuals for intelligent text extraction and analysis
"""

import streamlit as st
from datetime import datetime
import PyPDF2
import io
from rag_engine import RAGEngine
from monitoring_analytics import ResponseTimeTracker
from utils.theme_manager import apply_theme

# Apply theme globally
apply_theme()


def extract_text_from_pdf(pdf_file) -> str:
    """
    Extract text from uploaded PDF file
    
    Args:
        pdf_file: Streamlit UploadedFile object
        
    Returns:
        Extracted text content
    """
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_file.read()))
        text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"
        
        return text.strip()
    
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def render():
    """PDF upload and processing page with RAG integration"""
    # --- SAFETY INITIALIZATION ---
    if "analytics" not in st.session_state:
        # Import analytics class
        from monitoring_analytics import Analytics
        st.session_state.analytics = Analytics()
    
    if "pdf_count" not in st.session_state:
        st.session_state.pdf_count = 0
    
    if "rag_engine" not in st.session_state:
        # This prevents the "RAG Engine not initialized" error
        from aws_config import USE_AWS
        st.session_state.rag_engine = RAGEngine(use_aws=USE_AWS)
    # -----------------------------
    
    st.markdown("## 📚 PDF Upload & Processing")
    st.markdown("Upload your lab manuals, documentation, or study materials for intelligent text extraction and analysis.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        uploaded = st.file_uploader(
            "Choose PDF files",
            type=["pdf"],
            accept_multiple_files=False,
            help="Upload a PDF file to extract and analyze its content"
        )
        
        if uploaded:
            st.markdown(f"""
                <div class='status-box status-success'>
                    ✅ File received: <strong>{uploaded.name}</strong> ({uploaded.size / 1024:.1f} KB)
                </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # Process button
            col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
            with col_btn2:
                process_btn = st.button("🚀 Extract & Analyze Text", use_container_width=True)
            
            if process_btn:
                with st.spinner("📖 Extracting text from PDF..."):
                    # Extract text
                    extracted_text = extract_text_from_pdf(uploaded)
                    
                    if extracted_text.startswith("Error"):
                        st.markdown(f"""
                            <div class='status-box status-error'>
                                ❌ {extracted_text}
                            </div>
                        """, unsafe_allow_html=True)
                        return
                    
                    # Store in session state
                    if 'pdf_documents' not in st.session_state:
                        st.session_state.pdf_documents = []
                    
                    doc_id = f"doc_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                    
                    st.session_state.pdf_documents.append({
                        'id': doc_id,
                        'name': uploaded.name,
                        'text': extracted_text,
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'size': len(extracted_text)
                    })
                    
                    st.session_state.pdf_count += 1
                
                # Chunk the text with safety check
                with st.spinner("✂️ Chunking text for analysis..."):
                    # Safety check: Ensure rag_engine is initialized
                    if st.session_state.rag_engine is None:
                        st.error('❌ RAG Engine not initialized. Please refresh the page.')
                        return
                    
                    with ResponseTimeTracker(st.session_state.analytics, "pdf_processing"):
                        chunks = st.session_state.rag_engine.chunk_text(extracted_text)
                
                # Display results
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📊 Processing Results")
                
                col_r1, col_r2, col_r3 = st.columns(3)
                
                with col_r1:
                    st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-value'>{len(extracted_text):,}</div>
                            <div class='metric-label'>Characters</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_r2:
                    word_count = len(extracted_text.split())
                    st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-value'>{word_count:,}</div>
                            <div class='metric-label'>Words</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col_r3:
                    st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-value'>{len(chunks)}</div>
                            <div class='metric-label'>Chunks</div>
                        </div>
                    """, unsafe_allow_html=True)
                
                # Display extracted text preview
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📄 Extracted Text Preview")
                
                preview_length = min(2000, len(extracted_text))
                st.markdown(f"""
                    <div class='output-container' style='max-height: 400px;'>
{extracted_text[:preview_length]}
{'...' if len(extracted_text) > preview_length else ''}
                    </div>
                """, unsafe_allow_html=True)
                
                # Display chunk information
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 📦 Chunk Analysis")
                
                st.markdown(f"""
                    <div class='status-box status-info'>
                        ℹ️ Document has been split into <strong>{len(chunks)}</strong> semantic chunks (500-1000 tokens each) for efficient processing.
                    </div>
                """, unsafe_allow_html=True)
                
                # Show first few chunks
                with st.expander("🔍 View Chunk Details"):
                    for i, chunk in enumerate(chunks[:3]):
                        st.markdown(f"**Chunk {i+1}** ({chunk['token_count']} tokens)")
                        st.text(chunk['content'][:200] + "...")
                        st.markdown("---")
                    
                    if len(chunks) > 3:
                        st.markdown(f"*...and {len(chunks) - 3} more chunks*")
                
                # Download options
                st.markdown("<br>", unsafe_allow_html=True)
                col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
                
                with col_dl2:
                    st.download_button(
                        label="📥 Download Extracted Text",
                        data=extracted_text,
                        file_name=f"{uploaded.name.replace('.pdf', '')}_extracted.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
    
    with col2:
        st.markdown("""
            <div class='feature-card'>
                <div class='feature-icon' style='font-size: 2rem;'>📖</div>
                <div class='feature-title' style='font-size: 1.2rem;'>Features</div>
                <div class='feature-description' style='text-align: left;'>
                    <ul style='padding-left: 1.5rem;'>
                        <li>Text extraction from PDFs</li>
                        <li>Smart chunking (500-1000 tokens)</li>
                        <li>Token counting with tiktoken</li>
                        <li>Download extracted text</li>
                        <li>Chunk analysis & preview</li>
                    </ul>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Show uploaded documents history
        if st.session_state.get('pdf_documents'):
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
                <div class='feature-card'>
                    <div class='feature-icon' style='font-size: 1.5rem;'>📚</div>
                    <div class='feature-title' style='font-size: 1rem;'>Uploaded Docs</div>
                    <div class='feature-description' style='text-align: left; font-size: 0.85rem;'>
            """, unsafe_allow_html=True)
            
            for doc in st.session_state.pdf_documents[-5:]:  # Show last 5
                st.markdown(f"• {doc['name'][:20]}...")
            
            st.markdown("""
                    </div>
                </div>
            """, unsafe_allow_html=True)


if __name__ == "__main__":
    render()
else:
    render()
