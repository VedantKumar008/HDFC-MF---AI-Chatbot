# Deployment Guide

This guide covers deploying the HDFC Mutual Fund AI Assistant to production using free-tier services.

## Prerequisites

- GitHub repository with the project code
- Render account (free tier)
- Vercel account (free tier)
- Groq API key

## Backend Deployment (Render)

### 1. Create Render Web Service

1. Go to [render.com](https://render.com) and sign up/login
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `hdfc-mf-ai-assistant-api`
   - **Region**: Singapore (closest to India)
   - **Branch**: `main`
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

### 2. Configure Environment Variables

Add the following environment variables in Render:

| Variable | Value | Description |
|----------|-------|-------------|
| `GROQ_API_KEY` | Your Groq API key | Required for LLM generation |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model to use |
| `CORS_ORIGINS` | `https://your-vercel-app.vercel.app` | Frontend URL (update after Vercel deploy) |
| `DATA_PATH` | `./data/schemes` | Path to scheme JSON files |
| `FAISS_PATH` | `./data/faiss` | Path to FAISS index |
| `EMBEDDING_MODEL` | `all-MiniLM-L6-v2` | Embedding model name |
| `RAG_TOP_K` | `5` | Number of chunks to retrieve |
| `RAG_MIN_SCORE` | `0.4` | Minimum chunk similarity score |
| `RAG_MIN_TOP_SCORE` | `0.45` | Minimum top chunk score |

### 3. Deploy

1. Click "Create Web Service"
2. Render will build and deploy your backend
3. Wait for the deployment to complete
4. Note the backend URL (e.g., `https://hdfc-mf-ai-assistant-api.onrender.com`)

### 4. Verify Deployment

Check the health endpoint:
```bash
curl https://your-backend-url.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "phase": "4",
  "ready": true,
  "schemes_loaded": 21,
  "index_loaded": true,
  "chunk_count": 523
}
```

## Frontend Deployment (Vercel)

### 1. Create Vercel Project

1. Go to [vercel.com](https://vercel.com) and sign up/login
2. Click "Add New..." → "Project"
3. Import your GitHub repository
4. Configure the project:
   - **Framework Preset**: Next.js
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `.next`

### 2. Configure Environment Variables

Add the following environment variable in Vercel:

| Variable | Value | Description |
|----------|-------|-------------|
| `NEXT_PUBLIC_BACKEND_URL` | `https://your-backend-url.onrender.com` | Backend API URL from Render |

### 3. Deploy

1. Click "Deploy"
2. Vercel will build and deploy your frontend
3. Wait for the deployment to complete
4. Note the frontend URL (e.g., `https://your-app.vercel.app`)

### 4. Update CORS Configuration

Go back to Render and update the `CORS_ORIGINS` environment variable to include your Vercel URL:
```
https://your-app.vercel.app,http://localhost:3000
```

Redeploy the backend to apply the changes.

## GitHub Actions Configuration

The daily refresh workflow is already configured in `.github/workflows/daily-refresh.yml`. It will:

- Run daily at 9:00 AM IST
- Scrape latest data from Groww
- Rebuild the FAISS index
- Commit and push changes if data has changed

### Required GitHub Secrets

No additional secrets are required for the workflow as it uses the default GitHub Actions permissions.

### Manual Workflow Trigger

You can manually trigger the workflow:
1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Daily Data Refresh" workflow
4. Click "Run workflow"

## Post-Deployment Verification

### 1. Test Backend Health

```bash
curl https://your-backend-url.onrender.com/health
```

### 2. Test Frontend

1. Open your Vercel URL in a browser
2. Verify the loading screen appears
3. Wait for backend connection
4. Test a sample query: "What is the expense ratio of HDFC Large Cap Fund?"

### 3. Test Streaming

Verify that responses stream token-by-token (not all at once).

### 4. Test Compliance

Test that investment advice queries are blocked:
- "Should I invest in HDFC Large Cap Fund?"
- "Which fund is best for SIP?"

### 5. Test Session Context

1. Ask: "Tell me about HDFC Defence Fund"
2. Follow-up: "What is its expense ratio?"
3. Verify the follow-up uses context from the first question

## Free Tier Considerations

### Render Free Tier

- **Cold starts**: Backend may sleep after 15 minutes of inactivity
- **Spin-up time**: First request after sleep may take 30-60 seconds
- **Memory**: 512 MB RAM (sufficient for current index size)
- **CPU**: Shared CPU resources

### Vercel Free Tier

- **Serverless**: Functions scale automatically
- **Builds**: 100 builds per month
- **Bandwidth**: 100 GB per month
- **Domains**: Custom domains supported

### Mitigation Strategies

1. **Cold starts**: Frontend shows loading state during backend wake-up
2. **Rate limits**: Implement retry logic for failed requests
3. **Memory monitoring**: Keep FAISS index size manageable
4. **Daily refresh**: GitHub Actions ensures data stays fresh

## Troubleshooting

### Backend fails to start

- Check Render logs for errors
- Verify all environment variables are set
- Ensure `requirements.txt` includes all dependencies
- Check that data files (`data/schemes/`, `data/faiss/`) are committed

### Frontend can't connect to backend

- Verify `NEXT_PUBLIC_BACKEND_URL` is correct
- Check CORS configuration in Render
- Ensure backend health endpoint is accessible
- Check browser console for CORS errors

### Daily workflow fails

- Check GitHub Actions logs
- Verify scraper can access Groww
- Ensure FAISS index builds successfully
- Check git push permissions

### Slow response times

- Monitor Render logs for cold starts
- Consider upgrading to paid tier for consistent performance
- Optimize FAISS index size
- Check Groq API response times

## Monitoring

### Render Monitoring

- View metrics in Render dashboard
- Check response times and error rates
- Monitor memory usage
- Review deployment logs

### Vercel Monitoring

- View analytics in Vercel dashboard
- Check build success rate
- Monitor edge function performance
- Review deployment logs

### GitHub Actions Monitoring

- Check workflow run history
- Review success/failure rates
- Monitor execution time
- Check for rate limiting

## Security Considerations

1. **API Keys**: Never commit API keys to repository
2. **CORS**: Restrict CORS origins to your frontend domain
3. **Rate Limiting**: Implement rate limiting if needed
4. **Input Validation**: Backend validates all inputs
5. **HTTPS**: Both Render and Vercel use HTTPS by default

## Backup and Recovery

- **Data**: Scheme data and FAISS index are in git repository
- **Configuration**: Environment variables stored in platform settings
- **Code**: Version controlled in GitHub
- **Recovery**: Redeploy from GitHub if needed

## Cost Summary

| Service | Plan | Monthly Cost |
|---------|-------|-------------|
| Render (Web Service) | Free | $0 |
| Vercel (Frontend) | Free | $0 |
| GitHub Actions | Free | $0 |
| Groq API | Free Tier | $0 (within limits) |
| **Total** | | **$0** |

## Next Steps

1. Deploy backend to Render
2. Deploy frontend to Vercel
3. Update CORS configuration
4. Test end-to-end functionality
5. Monitor first few days of operation
6. Set up alerts for failures
