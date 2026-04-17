# Render Deployment Guide for Pulse of Humanity

## Quick Deploy Steps

1. **Connect GitHub Repository to Render**
   - Go to [Render Dashboard](https://dashboard.render.com/)
   - Click "New" → "Web Service"
   - Connect your GitHub repository

2. **Configure the Service**
   - **Name**: `pulse-of-humanity`
   - **Environment**: `Python`
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `gunicorn --config gunicorn.conf.py app:app`

3. **Set Environment Variables**
   ```
   FLASK_DEBUG=0
   RUN_UPDATER=1
   FLASK_SECRET_KEY=<generate-secure-key>
   POP_ANCHOR_MONTH=1
   POP_ANCHOR_DAY=1
   ADMIN_REANCHOR_TOKEN=<generate-secure-token>
   PORT=10000
   ```

4. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment to complete

## Environment Variables Required

- `FLASK_DEBUG`: Set to "0" for production
- `RUN_UPDATER`: Set to "1" to enable background annual anchor checks
- `FLASK_SECRET_KEY`: Generate a secure random key
- `POP_ANCHOR_MONTH` / `POP_ANCHOR_DAY`: Configure the yearly authoritative re-anchor date
- `ADMIN_REANCHOR_TOKEN`: Optional token for the manual `POST /admin/reanchor` endpoint
- `PORT`: Will be set automatically by Render (defaults to 10000)

## Files Created for Deployment

- `render.yaml`: Render service configuration
- `gunicorn.conf.py`: Production server configuration
- `start.sh`: Startup script (alternative)
- Enhanced health check at `/health`

## Troubleshooting

### Common Issues:
1. **Build fails**: Check requirements.txt dependencies
2. **App won't start**: Check environment variables
3. **502 errors**: Ensure app binds to 0.0.0.0:PORT
4. **SSL issues**: HTTPS redirect is enabled in production

### Debugging:
- Check Render logs in the dashboard
- Use the enhanced `/health` endpoint
- Verify environment variables are set correctly

## Health Check

The app includes an enhanced health check at `/health` that returns:
```json
{
  "status": "healthy",
  "timestamp": "2025-09-22T22:07:18Z",
  "version": "1.0.0",
  "population": 8000000000,
  "debug_mode": false
}
```

## Performance Notes

- Uses gunicorn with 2 workers
- Includes connection pooling and request limits
- Mobile-responsive design with optimized assets
- Background annual anchor checks enabled