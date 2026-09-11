# Deployment Guide: Enlace Examples on Render

This document covers deploying the FastAPI reference implementation to [Render](https://render.com).

## Architecture

Two separate Render services:

| Service | Trigger | Branch | Database | URL Pattern |
|---------|---------|--------|----------|------------|
| **dev** | Every push to `main` | `main` | Postgres (dev) | `enlace-examples-dev.onrender.com` |
| **prod** | Manual (release tags) | Tagged releases | Postgres (prod) | `enlace-examples-prod.onrender.com` |

Both use the same FastAPI code; databases are kept separate for safety.

## Prerequisites

1. **Render account**: https://render.com (free tier works for dev/testing)
2. **GitHub repository**: enlace-examples pushed and accessible
3. **Neon Postgres databases**: One for dev, one for prod (free tier available at https://neon.tech)

## Step 1: Create Neon Postgres Databases

### Dev Database

1. Go to https://console.neon.tech
2. Create a new project: `enlace-examples-dev`
3. Copy the connection string, it will look like:
   ```
   postgresql://user:password@ep-xyz.us-east-1.neon.tech/dbname
   ```
4. Save this as `NEON_DEV_URL` — you'll need it for the dev Render service

### Prod Database

1. Create another project: `enlace-examples-prod`
2. Copy the connection string as `NEON_PROD_URL`

## Step 2: Create Render Services

### Dev Service

1. Go to https://dashboard.render.com/services
2. Click **New +** → **Web Service**
3. **Connect Repository**:
   - Select your GitHub account
   - Find and select `get-enlace/enlace-examples`
   - Branch: `main`
   - Auto-deploy: ✓ Yes

4. **Configuration**:
   - **Name**: `enlace-examples-dev`
   - **Root Directory**: `fastapi` (since it's a monorepo)
   - **Runtime**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free (or Starter if you want more reliability)

5. **Environment Variables**:
   - `DATABASE_URL`: (paste your `NEON_DEV_URL` here)
   - `PORT`: `10000`

6. Click **Create Web Service**

The dev instance will auto-deploy whenever you push to `main`.

### Prod Service

Repeat the same process with these differences:

1. **Name**: `enlace-examples-prod`
2. **Branch**: Leave blank (you'll trigger this manually via GitHub Actions)
3. **Auto-deploy**: ✗ No (we'll deploy via GitHub workflow on release tags)
4. **Environment Variables**:
   - `DATABASE_URL`: (paste your `NEON_PROD_URL` here)

Note: For manual deployment, you'll need a **Render API key** (see Step 3 below).

## Step 3: Get Render Deployment Token

For GitHub Actions to auto-deploy, we need a Render API key:

1. Go to https://dashboard.render.com/account
2. Scroll to **API Keys**
3. Click **Create API Key**
4. Copy the key and save it somewhere safe (you'll only see it once)
5. Go to your GitHub repo → **Settings** → **Secrets and variables** → **Actions**
6. Create a new secret: `RENDER_API_KEY` = (paste the Render API key)

## Step 4: Configure GitHub Secrets

In your GitHub repo (`get-enlace/enlace-examples`), add:

**Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Secret | Value |
|--------|-------|
| `RENDER_API_KEY` | Your Render API key (from Step 3) |

That's it! GitHub Actions workflows will use this to trigger deployments.

## Step 5: Verify Deployment

Once the Render service is created:

1. **Dev instance** should auto-deploy on next push to `main`
   - Watch the deploy at: https://dashboard.render.com/services/enlace-examples-dev
   - Access at: https://enlace-examples-dev.onrender.com/enlace

2. **Prod instance** deploys when you create a release in GitHub:
   - Go to your GitHub repo → **Releases** → **Create a new release**
   - Tag: `v0.1.0` (or similar)
   - GitHub Actions will automatically trigger the prod deployment
   - Access at: https://enlace-examples-prod.onrender.com/enlace

## Monitoring

### Live Logs

1. Dev: https://dashboard.render.com/services/enlace-examples-dev
2. Prod: https://dashboard.render.com/services/enlace-examples-prod

Each service shows:
- Deployment status (building, deploying, live)
- Application logs in real-time
- Error messages if something fails

### Health Checks

Each Render service auto-performs health checks on the `/health` endpoint (if you add one) or via the root `/docs` endpoint (our FastAPI Swagger UI is alive).

## Troubleshooting

### Deployment Fails

1. Check the Render logs for the specific error
2. Common issues:
   - **Missing `requirements.txt`**: Make sure it's in the `fastapi/` root
   - **Missing environment variables**: Verify `DATABASE_URL` is set in Render dashboard
   - **Port mismatch**: Start command uses `$PORT` env var (Render sets this dynamically)

### Database Connection Errors

1. Verify the Neon connection string is correct (check Settings → Connection string)
2. Ensure Neon's IP whitelist allows all IPs (should be default for free tier)
3. Test locally with `export DATABASE_URL="..."; python -m app.main`

### High Memory Usage

If Render is spinning down your free-tier service:
- Upgrade to a paid plan
- Or use Render's scheduled cleanup (Services → Settings → Cron jobs)

## Local Testing with Neon Databases

To test against a real Postgres database locally:

```bash
export DATABASE_URL="postgresql://user:pass@host/dbname"
python -m app.main
```

The app will:
1. Create all tables on startup
2. Seed fixtures (upsert-if-missing)
3. Serve requests normally

## CI/CD Pipeline Summary

```
push to main
    ↓
GitHub Actions runs tests (if configured)
    ↓
Auto-deploy to Render dev service
    ↓
Dev instance live at enlace-examples-dev.onrender.com

---

Create GitHub Release tag
    ↓
GitHub Actions trigger deploy workflow
    ↓
Call Render API to deploy prod service
    ↓
Prod instance live at enlace-examples-prod.onrender.com
```

## Next: Setting up GitHub Workflows

Once your Render services are created, see `.github/workflows/` for:
- `test.yml` — Runs tests on every push (optional)
- `deploy-dev.yml` — Auto-deploys dev instance on push to main
- `deploy-prod.yml` — Manual deploys prod instance on GitHub release

(These will be created in the next section.)
