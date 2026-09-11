# Deployment Guide: Enlace Examples on Render

FastAPI reference implementation, deployed as a **single instance** that stays synced with the latest adapter and UI.

## Architecture

**One Render service** that deploys when:
1. **Direct changes** to `fastapi/` folder in this repo
2. **Adapter updates** triggered by `enlace-python` (via `repository_dispatch`)

This ensures:
- Always using latest `enlace-fastapi` adapter
- Adapter always matches latest `enlace-ui` (because adapter auto-updates on UI changes)
- No manual version management

```
enlace-ui deploys
  ↓ triggers
enlace-python adapter redeploy
  ↓ triggers (repository_dispatch)
enlace-examples redeploy
  ↓
Single Render instance always in sync
```

## Prerequisites

1. **Render account**: https://render.com (free tier works)
2. **Neon Postgres database**: https://neon.tech (free tier available)
3. **GitHub repository**: `get-enlace/enlace-examples` pushed

## Step 1: Create Neon Postgres Database

1. Go to https://console.neon.tech
2. Create a new project: `enlace-examples`
3. Copy the connection string:
   ```
   postgresql://user:password@ep-xyz.us-east-1.neon.tech/dbname
   ```

## Step 2: Create Render Web Service

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. **Connect Repository**:
   - Select GitHub account
   - Find `get-enlace/enlace-examples`
   - Branch: `main`

4. **Configuration**:
   - **Name**: `enlace-examples`
   - **Root Directory**: `fastapi`
   - **Runtime**: `Python 3.11`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

5. **Environment Variables**:
   - `DATABASE_URL`: (paste your Neon connection string)

6. **Auto-Deploy**: Leave OFF for now (we'll use deploy hooks)

7. Click **Create Web Service** and wait for it to finish building

## Step 3: Get Render Deploy Hook

Deploy hooks let workflows trigger deployments without API keys.

1. In Render dashboard → Service (`enlace-examples`) → Settings
2. Scroll to **Deploy Hooks**
3. Click **Create Deploy Hook**
4. Name: `GitHub` (or anything)
5. Copy the hook URL: `https://api.render.com/deploy/srv_...?key=...`

## Step 4: Add GitHub Secret

1. Go to your repo → **Settings** → **Secrets and variables** → **Actions**
2. Click **New repository secret**:
   - **Name**: `RENDER_DEPLOY_HOOK`
   - **Value**: (paste the hook URL from Step 3)

## Step 5: Verify Deployment

### Test Direct Changes

1. Make a small change to `fastapi/README.md`
2. Commit and push to `main`
3. Go to https://github.com/get-enlace/enlace-examples/actions
4. Watch the `Deploy FastAPI to Render` workflow run
5. Render should auto-deploy
6. Monitor at: https://dashboard.render.com/services/enlace-examples

### Access the Live Instance

- **Canvas**: https://enlace-examples.onrender.com/enlace
- **API Docs**: https://enlace-examples.onrender.com/docs
- **Products**: https://enlace-examples.onrender.com/products

### Test Auth

```bash
curl -X POST https://enlace-examples.onrender.com/oauth/token \
  -d "grant_type=password&username=alice@example.com&password=demo-password-123" \
  -H "Content-Type: application/x-www-form-urlencoded"
```

Should return:
```json
{
  "accessToken": "...",
  "tokenType": "Bearer",
  "expiresIn": 3600,
  "scope": "customer"
}
```

## Step 6: Set Up Adapter Sync (enlace-python)

When a new `enlace-fastapi` version is published, it should trigger a redeploy of this instance.

In the **`enlace-python` repo**, add a deploy workflow that triggers this repo:

```yaml
# In enlace-python/.github/workflows/deploy.yml (or similar)
- name: Notify enlace-examples to redeploy
  if: success()  # Only after successful adapter deployment
  run: |
    curl -X POST \
      -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" \
      -H "Accept: application/vnd.github.v3+raw" \
      https://api.github.com/repos/get-enlace/enlace-examples/dispatches \
      -d '{"event_type":"enlace-fastapi-deployed"}'
```

Once that's in place, whenever `enlace-python` deploys a new adapter version, it automatically triggers an `enlace-examples` redeploy.

## Monitoring & Maintenance

### Live Logs

https://dashboard.render.com/services/enlace-examples

Shows:
- Deployment status (building, deploying, live)
- Application logs in real-time
- Any errors during startup

### Recent Deployments

**Render dashboard** → Service → **Deployments** tab

Lists all past deploys with:
- Trigger (GitHub push, deploy hook, manual)
- Status (success/failed)
- Duration
- Logs

### Manual Redeploy

If needed:
1. Render dashboard → Service → **Deployments** tab
2. Click **Trigger Deploy** (top right)

Or via GitHub:
1. This repo → Actions → `Deploy FastAPI to Render` → Run workflow

### Restart Service

If env vars change and you want immediate restart (without redeploying):
1. Render dashboard → Service → **Settings** → Danger Zone
2. Click **Restart**

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Deployment fails with "module not found" | Check `requirements.txt` is in `fastapi/` root |
| "RENDER_DEPLOY_HOOK secret not found" | Add the secret to GitHub (Step 4) |
| App starts but can't connect to database | Verify `DATABASE_URL` is set in Render → Environment |
| Free tier keeps spinning down | Upgrade plan, or use a ping service to keep it alive |
| Adapter didn't trigger a redeploy | Manually trigger via Render dashboard for now; set up enlace-python workflow later |

## Deployment Triggers Summary

```
Event                          Workflow         Deploy?
─────────────────────────────────────────────────────
Push to fastapi/ folder        deploy.yml       ✅ Yes
Push to other folders          deploy.yml       ❌ No
enlace-python dispatches       deploy.yml       ✅ Yes
Manual trigger in GitHub       deploy.yml       ✅ Yes
Manual trigger in Render       Render API       ✅ Yes
```

## Environment Variables

**In Render Service** (set in dashboard):

- `DATABASE_URL` — Neon Postgres connection string
  - Format: `postgresql://user:pass@host/dbname`
- `PORT` — Set automatically by Render to a random port
- `DEMO_CUSTOMER_EMAIL` — (optional, default: `alice@example.com`)
- `DEMO_CUSTOMER_PASSWORD` — (optional, default: `demo-password-123`)
- `ADMIN_CLIENT_ID` — (optional, default: `admin-service`)
- `ADMIN_CLIENT_SECRET` — (optional, default: `admin-service-secret`)
- `CARRIER_API_KEY` — (optional, default: `carrier-demo-key`)

See `fastapi/README.md` for all available env vars.

## CI/CD Pipeline

```
┌─────────────────────────────────────────────────────────┐
│  enlace-ui change                                       │
│  ↓                                                      │
│  enlace-ui auto-deploys                                │
│  ↓                                                      │
│  enlace-python detects @get-enlace/ui update          │
│  ↓                                                      │
│  enlace-python auto-deploys new adapter version       │
│  ↓                                                      │
│  enlace-python triggers repository_dispatch            │
│  on get-enlace/enlace-examples                         │
│  ↓                                                      │
│  GitHub Actions: deploy.yml runs                       │
│  ↓                                                      │
│  Curl → Render deploy hook                            │
│  ↓                                                      │
│  Render pulls latest code (fastapi/ + new adapter)    │
│  ↓                                                      │
│  Rebuild with: pip install -r requirements.txt        │
│  ↓                                                      │
│  Deploy ✅ → Live with latest adapter + UI            │
└─────────────────────────────────────────────────────────┘
```

---

For quick reference, see `SETUP_CHECKLIST.md`.
