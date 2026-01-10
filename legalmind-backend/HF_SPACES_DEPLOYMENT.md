# HuggingFace Spaces Deployment Guide

## Prerequisites

1. **HuggingFace Account** - [Create account](https://huggingface.co/)
2. **HF CLI** - Install with `pip install huggingface-hub`
3. **Docker** - Optional but recommended for local testing
4. **Git** - For version control

## Environment Variables Required

Create a `.env` file in the backend directory with:

```env
# Supabase Configuration (REQUIRED)
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key_here

# Optional: API Keys for third-party services
# OPENAI_API_KEY=your_openai_key_if_using_gpt
# HUGGINGFACE_API_KEY=your_hf_api_key_if_needed

# Server Configuration (HF Spaces defaults these)
PORT=7860
HOST=0.0.0.0
```

## Step 1: Create HuggingFace Space

```bash
# Login to HuggingFace
huggingface-cli login

# Create a new Space (via web interface or CLI)
# Go to https://huggingface.co/new-space
# 1. Select "Docker" as the Space SDK
# 2. Set visibility to "Private" or "Public"
# 3. Create Space
```

## Step 2: Clone Space Repository

```bash
# Clone your new space
git clone https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
cd YOUR_SPACE_NAME

# Add the backend code
# Copy all files from legalmind-backend/ to this directory
```

## Step 3: Setup Files

Ensure these files are in your Space root directory:

- `Dockerfile` - Container configuration
- `.dockerignore` - Exclude unnecessary files
- `app.py` - Entry point for HF Spaces
- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies
- `ml_pipeline/` - ML modules
- All other backend code

## Step 4: Configure secrets.env

**Important**: Do NOT commit `.env` to Git!

In your HuggingFace Space settings:
1. Go to Settings → Secrets
2. Add the environment variables:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`

HF Spaces will automatically inject these as environment variables.

## Step 5: Push to HuggingFace Spaces

```bash
# Add and commit your files
git add .
git commit -m "Initial LegalMind backend deployment"

# Push to HF Spaces (this triggers automatic build/deployment)
git push

# View logs: https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME/logs
```

## Step 6: Monitor Deployment

1. **Space Page**: https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
2. **View Logs**: Scroll down on the Space page to see build/runtime logs
3. **Test API**: Once deployed, access at:
   - Health Check: `https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/health`
   - API Docs: `https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/docs`
   - Swagger UI: Same as above, interactive API explorer

## API Endpoints

After deployment, your API will be available at:
```
https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space/api/v1/
```

### Key Endpoints:
- **POST** `/api/v1/upload` - Upload document for analysis
- **GET** `/api/v1/job/{job_id}` - Check analysis status
- **GET** `/api/v1/document/{document_id}` - Get document details
- **POST** `/api/v1/chat` - Chat about document
- **GET** `/api/v1/report/{document_id}` - Download analysis report
- **GET** `/health` - Health check

## Frontend Configuration

Update your frontend `.env.production`:

```env
VITE_API_BASE_URL=https://YOUR_USERNAME-YOUR_SPACE_NAME.hf.space
```

Then rebuild and deploy frontend.

## Troubleshooting

### Build Fails
- Check logs in Space settings
- Verify all required files are present
- Ensure no circular imports in code
- Check file permissions

### Runtime Errors
- Check environment variables are set in Secrets
- Verify Supabase credentials are correct
- Check database has proper tables and RLS policies
- Review application logs in Space page

### Timeout Issues
- HF Spaces has limited resources; model loading may take time
- Consider using cached models
- Pre-warm the model on startup

### Memory Issues
- Switch to smaller models if available
- Optimize ML pipeline for memory efficiency
- Use `faiss-cpu` instead of GPU-based alternatives
- Monitor with Space's resource dashboard

## Performance Optimization

### For HF Spaces:

1. **Model Caching**
   ```python
   # Already implemented in get_risk_pipeline()
   # Models are cached globally to avoid reloading
   ```

2. **File Cleanup**
   ```python
   # Already implemented in main.py
   # Temporary files deleted after processing
   ```

3. **Database Optimization**
   - Use Supabase for data storage (not local files)
   - Leverage RLS for security
   - Use indexes for faster queries

4. **Batch Processing**
   - Process multiple chunks together when possible
   - Stream large uploads
   - Cache embeddings

## Updating Deployment

To update the Space after initial deployment:

```bash
# Make changes to your code
# ...

# Commit changes
git add .
git commit -m "Description of changes"

# Push to HF Spaces (auto-deploys)
git push
```

The Space will rebuild automatically and restart with the new code.

## Scaling Considerations

### When to Upgrade:
- High request volume
- Long processing times
- Out of memory errors

### Upgrade Options:
1. **Persistent Storage** - Use Supabase instead of local files
2. **GPU Resources** - Upgrade Space tier (may incur costs)
3. **Private Spaces** - For production deployments
4. **Custom Domain** - Map your own domain

## Security Best Practices

✓ **Already Implemented:**
- Environment variables for secrets (not in code)
- CORS properly configured
- Input validation in FastAPI
- RLS in Supabase database
- File upload size limits

**Additional Recommendations:**
- Keep Space as Private if possible
- Rotate Supabase keys regularly
- Monitor API usage for abuse
- Add rate limiting for public access
- Use HTTPS only (automatic with HF Spaces)

## Support & Resources

- **HF Spaces Docs**: https://huggingface.co/docs/hub/spaces
- **HF Spaces Discord**: Join the community for help
- **Backend Repo**: https://github.com/[your-repo]
- **Documentation**: See DEPLOYMENT_GUIDE.md in root

---

**Deployment Status**: Ready for HuggingFace Spaces ✅
