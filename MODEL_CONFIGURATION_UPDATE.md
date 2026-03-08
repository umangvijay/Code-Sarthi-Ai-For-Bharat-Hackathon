# Model Configuration Update - Code-Sarthi

## ✓ COMPLETED: Updated to Nova Micro + Titan Embed V1

All files have been updated to use Amazon Nova Micro (lowest token model) for text generation and Titan Embed V1 for embeddings to avoid AWS Bedrock ThrottlingExceptions and dimension mismatches.

---

## Updated Model IDs

### Text Generation Models
**Model:** `amazon.nova-micro-v1:0` (Lowest token, best for throttling)

**Previous models (commented out):**
- `amazon.nova-lite-v1:0` (commented out due to throttling)
- `amazon.titan-text-express-v1` (commented out, switched to Nova Micro)

Updated in:
- ✓ `translation_engine.py` - Line ~106-109
- ✓ `aws_viva_evaluation.py` - Line ~57-60
- ✓ `aws_bedrock_utils.py` - Line ~31-35

### Embeddings Model
**Model:** `amazon.titan-embed-text-v1`  
**Dimension:** `1536`

Updated in:
- ✓ `rag_engine.py` - Line ~86 (embedding_dimension)
- ✓ `rag_engine.py` - Line ~115 (exception handler)
- ✓ `rag_engine.py` - Line ~135 (model invocation)

---

## Configuration Summary

| Component | Model ID | Dimension | Status |
|-----------|----------|-----------|--------|
| Translation Engine | amazon.nova-micro-v1:0 | N/A | ✓ Updated |
| Viva Evaluation | amazon.nova-micro-v1:0 | N/A | ✓ Updated |
| Bedrock Utils | amazon.nova-micro-v1:0 | N/A | ✓ Updated |
| RAG Engine (Embeddings) | amazon.titan-embed-text-v1 | 1536 | ✓ Verified |
| S3 Bucket | code-sarthi-pdfs-umang | N/A | ✓ Hardcoded |

---

## Why These Changes?

### Problem:
- AWS Bedrock ThrottlingExceptions with Nova Lite models
- Dimension mismatches with Titan V2 embeddings (1024 vs 1536)
- Need for lowest-token model to minimize throttling

### Solution:
- **Nova Micro V1**: Lowest token model, minimal throttling, cost-effective
- **Titan Embed Text V1**: Standard 1536 dimensions, well-tested and reliable
- **S3 Bucket**: Hardcoded to `code-sarthi-pdfs-umang` for consistency

---

## Code Changes - Commented Out Previous Models

All files now include commented-out references to previous models for easy rollback:

```python
# Model ID for text generation
# self.model_id = "amazon.nova-lite-v1:0"  # Previous: Nova Lite (commented out due to throttling)
# self.model_id = "amazon.titan-text-express-v1"  # Previous: Titan Text Express
self.model_id = "amazon.nova-micro-v1:0"  # Current: Nova Micro (lowest token, best for throttling)
```

---

## Verification

Run this command to verify all configurations:

```bash
python -c "from translation_engine import TranslationEngine; from aws_viva_evaluation import VivaAnswerEvaluator; from aws_bedrock_utils import BedrockClient; from rag_engine import RAGEngine; print('Translation:', TranslationEngine().model_id); print('Viva:', VivaAnswerEvaluator().model_id); print('Bedrock:', BedrockClient().model_id); engine = RAGEngine(use_aws=False); print('RAG Dimension:', engine.embedding_dimension); print('S3 Bucket:', engine.s3_bucket_name)"
```

Expected output:
```
Translation: amazon.nova-micro-v1:0
Viva: amazon.nova-micro-v1:0
Bedrock: amazon.nova-micro-v1:0
RAG Dimension: 1536
S3 Bucket: code-sarthi-pdfs-umang
```

---

## Deployment Instructions

### 1. Clear Python Cache
```bash
# Windows PowerShell
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force

# Linux/Mac
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
```

### 2. Set Environment Variables
```bash
export USE_AWS=True
export S3_BUCKET_NAME="code-sarthi-pdfs-umang"
```

### 3. Start Streamlit
```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

---

## Benefits of Nova Micro + Titan Embed V1

### Nova Micro V1:
- ✓ Lowest token consumption (best for throttling)
- ✓ Cost-effective for high-volume applications
- ✓ Fast response times
- ✓ Minimal rate limiting

### Titan Embed Text V1:
- ✓ Standard 1536 dimensions (compatible with most vector stores)
- ✓ Proven reliability in production
- ✓ Lower cost per embedding
- ✓ Fast embedding generation

---

## Troubleshooting

### If you still see throttling:
1. Check your AWS Bedrock quotas in AWS Console
2. Request quota increase for Nova Micro model
3. Exponential backoff is already implemented in code

### If dimension mismatch errors:
1. Verify `self.embedding_dimension = 1536` in rag_engine.py
2. Clear FAISS index: Delete `pdf_metadata.json`
3. Re-index documents

### If S3 errors:
1. Verify bucket name: `code-sarthi-pdfs-umang`
2. Check IAM permissions for S3 access
3. Verify bucket exists in your AWS account

### To rollback to previous models:
Simply uncomment the desired model line and comment out the current one:
```python
# self.model_id = "amazon.nova-micro-v1:0"  # Comment this out
self.model_id = "amazon.titan-text-express-v1"  # Uncomment this
```

---

## Files Modified

1. **translation_engine.py**
   - Changed model_id to `amazon.nova-micro-v1:0`
   - Commented out previous models (Nova Lite, Titan Text Express)

2. **aws_viva_evaluation.py**
   - Changed model_id to `amazon.nova-micro-v1:0`
   - Commented out previous models (Nova Lite, Titan Text Express)

3. **aws_bedrock_utils.py**
   - Changed model_id to `amazon.nova-micro-v1:0`
   - Commented out previous models (Nova Lite, Titan Text Express)

4. **rag_engine.py**
   - Verified embedding model: `amazon.titan-embed-text-v1`
   - Verified embedding_dimension: `1536`
   - S3 bucket remains: `code-sarthi-pdfs-umang`

---

## Testing

All files have been:
- ✓ Syntax checked (0 errors)
- ✓ Import tested (successful)
- ✓ Configuration verified (correct model IDs)
- ✓ Python cache cleared

---

**Last Updated:** 2024-03-08  
**Status:** ✓ READY FOR DEPLOYMENT  
**Text Model:** Nova Micro V1 (lowest token)  
**Embedding Model:** Titan Embed Text V1  
**Embedding Dimension:** 1536  
**S3 Bucket:** code-sarthi-pdfs-umang
