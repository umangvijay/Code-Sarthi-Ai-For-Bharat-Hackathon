# AWS Setup Checklist for Code-Sarthi

## Issues Fixed

### 1. ✅ ImportError Fixed
- **Problem**: `cannot import name 'Analytics' from 'monitoring_analytics'`
- **Solution**: Changed import from `Analytics` to `UsageAnalytics` (correct class name)
- **File**: `pages/3_📚_PDF_Upload.py` line 47

### 2. ⚠️ ValidationException - Model Access Required

**Error**: `The provided model identifier is invalid`

This means the model isn't available in your AWS account/region. Follow these steps:

## AWS Console Setup Steps

### Step 1: Verify Region
1. Open AWS Console
2. Check top-right corner - ensure you're in **Oregon (us-west-2)**
3. If not, switch to us-west-2

### Step 2: Enable Model Access
1. Go to **Amazon Bedrock** service
2. Click **Model access** in left sidebar
3. Click **Manage model access** button
4. Find and enable these models:
   - ✅ **Amazon Titan Text Embeddings V1** (for PDF upload)
   - ✅ **Google Gemma 3 12B Instruct** (for code explanation, translation, viva)
5. Click **Save changes**
6. Wait 2-5 minutes for access to be granted

### Step 3: Verify Model IDs
The following model IDs are configured in your code:

| File | Model ID | Purpose |
|------|----------|---------|
| `rag_engine.py` | `amazon.titan-embed-text-v1` | PDF embeddings (1536 dimensions) |
| `translation_engine.py` | `google.gemma-3-12b-it-v1:0` | Hinglish translation |
| `aws_viva_evaluation.py` | `google.gemma-3-12b-it-v1:0` | Viva answer evaluation |
| `aws_bedrock_utils.py` | `google.gemma-3-12b-it-v1:0` | Code explanation |

### Step 4: Check IAM Permissions
Your IAM role/user needs these permissions:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": [
        "arn:aws:bedrock:us-west-2::foundation-model/amazon.titan-embed-text-v1",
        "arn:aws:bedrock:us-west-2::foundation-model/google.gemma-3-12b-it-v1:0"
      ]
    }
  ]
}
```

## Testing After Setup

### Test 1: Check Model Access
Run this in your terminal:
```bash
aws bedrock list-foundation-models --region us-west-2 --query "modelSummaries[?contains(modelId, 'titan-embed') || contains(modelId, 'gemma')].modelId"
```

Expected output should include:
- `amazon.titan-embed-text-v1`
- `google.gemma-3-12b-it-v1:0`

### Test 2: Test Embedding Model
```bash
python -c "from rag_engine import RAGEngine; engine = RAGEngine(use_aws=True); print('✓ RAG Engine initialized')"
```

### Test 3: Test Gemma Model
```bash
python -c "from aws_bedrock_utils import BedrockClient; client = BedrockClient(); print('✓ Bedrock Client initialized')"
```

## Common Issues

### Issue: "Model not found"
- **Cause**: Model access not enabled in Bedrock console
- **Fix**: Follow Step 2 above

### Issue: "Access denied"
- **Cause**: IAM permissions missing
- **Fix**: Add bedrock:InvokeModel permission (Step 4)

### Issue: "Throttling exception"
- **Cause**: Too many requests
- **Fix**: Add retry logic (already implemented) or request quota increase

### Issue: "Invalid region"
- **Cause**: Wrong region in code or console
- **Fix**: Ensure all files use `us-west-2` (already updated)

## Verification Checklist

- [ ] AWS Console shows region as **us-west-2 (Oregon)**
- [ ] Model access page shows **Amazon Titan Text Embeddings V1** as **Enabled**
- [ ] Model access page shows **Google Gemma 3 12B Instruct** as **Enabled**
- [ ] IAM role has **bedrock:InvokeModel** permission
- [ ] Environment variable `USE_AWS=True` is set
- [ ] AWS credentials are configured (`aws configure` or IAM role)

## Next Steps

1. Complete the checklist above
2. Restart your Streamlit app: `streamlit run app.py`
3. Try uploading a PDF to test the embedding model
4. Try code explanation to test the Gemma model

## Support

If issues persist after following this checklist:
1. Check CloudWatch Logs for detailed error messages
2. Verify your AWS account has Bedrock access (not all accounts have it by default)
3. Contact AWS Support if model access requests are pending for >24 hours
