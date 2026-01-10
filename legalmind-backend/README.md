# LegalMind Backend

AI-powered legal contract analysis backend powered by FastAPI, ML models, and Supabase.

## Overview

This backend provides intelligent contract analysis through:
- **Risk Detection** - Identifies risky clauses in contracts
- **RAG System** - Retrieves context-aware legal advice
- **Chat Interface** - Discuss contracts with AI assistant
- **Vector Database** - Semantic search with FAISS
- **Cloud Storage** - Secure data storage with Supabase

## Quick Start

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your Supabase credentials

# Run server
python -m uvicorn main:app --reload --port 8000

# API Docs: http://localhost:8000/docs
```

### Docker

```bash
# Build image
docker build -t legalmind-backend .

# Run container
docker run -p 8000:8000 --env-file .env legalmind-backend

# For HuggingFace Spaces (port 7860)
docker run -p 7860:7860 --env-file .env legalmind-backend
```

## Architecture

### Core Modules

- **`main.py`** - FastAPI application and endpoints
- **`ml_pipeline/`**
  - `Document_loader.py` - PDF extraction and chunking
  - `risk_detector.py` - ML model for risk classification
  - `LLM_advisory.py` - LLM-based analysis and RAG
  - `chatbot.py` - AI assistant for document chat
  - `supabase_manager.py` - Database and storage operations

### Data Flow

```
1. Upload PDF
   ↓
2. Extract & Chunk (Document_loader)
   ↓
3. Risk Detection (risk_detector)
   ↓
4. LLM Analysis (LLM_advisory)
   ↓
5. Store in Supabase (supabase_manager)
   ↓
6. Clean temporary files
```

## API Endpoints

### Document Analysis

- **POST** `/api/v1/upload` - Upload document for analysis
- **GET** `/api/v1/job/{job_id}` - Check processing status
- **GET** `/api/v1/document/{document_id}` - Get analysis results
- **GET** `/api/v1/report/{document_id}` - Download report

### Chat & Interaction

- **POST** `/api/v1/chat` - Chat about specific document
- **POST** `/api/v1/chatbot` - General legal assistance
- **GET** `/api/v1/chatbot/suggestions` - Get smart suggestions

### Health & Status

- **GET** `/health` - Health check endpoint
- **GET** `/` - API info and documentation link

## Environment Variables

**Required:**
```env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

**Optional:**
```env
PORT=8000
HOST=0.0.0.0
OPENAI_API_KEY=optional_for_gpt_models
HUGGINGFACE_API_KEY=optional_for_hf_models
```

## Database Schema

### Tables
- **documents** - Document metadata and status
- **risky_chunks** - Individual risky clauses with analysis
- **chat_history** - Conversation history with documents

### Storage Buckets
- **vector-stores** - FAISS vector indices for RAG
- **reports** - Generated analysis reports

All protected by Row-Level Security (RLS) policies.

## Performance

### Optimizations
- Model caching (load once, reuse)
- Batch processing for chunks
- File cleanup after analysis
- Vector embeddings caching
- Streaming uploads for large files

### Resource Requirements
- **CPU**: 2+ cores recommended
- **RAM**: 4GB minimum, 8GB+ for production
- **GPU**: Optional (CPU works fine with faiss-cpu)
- **Storage**: ~10GB for models + dynamic for uploads

## Deployment

### HuggingFace Spaces
See [HF_SPACES_DEPLOYMENT.md](./HF_SPACES_DEPLOYMENT.md) for detailed guide.

### Docker Compose
```bash
docker-compose up
```

### Vercel/Railway
1. Use `app.py` as entrypoint
2. Set PORT to 3000 (or platform default)
3. Configure environment variables
4. Deploy

## Testing

```bash
# Test health endpoint
curl http://localhost:8000/health

# Test API documentation
curl http://localhost:8000/docs

# Upload test document
curl -X POST http://localhost:8000/api/v1/upload \
  -F "file=@test.pdf" \
  -F "user_id=test-user-123"
```

## Security

- ✅ Environment variables for secrets
- ✅ CORS configuration for frontend
- ✅ Input validation with Pydantic
- ✅ Row-Level Security in database
- ✅ File upload size limits (50MB)
- ✅ HTTPS enforced in production

## Troubleshooting

### Model Loading Slow
- First request loads the model (~2-3 minutes)
- Subsequent requests use cache
- This is normal behavior

### Out of Memory
- Reduce chunk size in PipelineConfig
- Use GPU if available
- Process smaller files

### Supabase Errors
- Verify credentials in .env
- Check database tables exist
- Verify RLS policies are set

### API Not Responding
- Check server logs
- Verify port is not in use
- Check environment variables loaded

## Contributing

See [IMPLEMENTATION_GUIDE.md](../IMPLEMENTATION_GUIDE.md)

## License

Proprietary - LegalMind

## Support

- 📧 Email: support@legalmind.ai
- 📚 Docs: See root README.md
- 🐛 Issues: Report via GitHub issues

---

**Status**: Production Ready ✅
**Version**: 1.0.0
**Last Updated**: December 2024
