# Deployment Setup Checklist

Single Render instance, auto-synced with latest adapter and UI.

## Phase 1: Database (Neon) — 5 min

- [ ] Create Neon account: https://console.neon.tech
- [ ] Create project `enlace-examples`
- [ ] Copy connection string (format: `postgresql://user:pass@host/db`)
- [ ] Save as `$NEON_URL`

**Verify:**
```bash
psql $NEON_URL -c "SELECT version();"
```

## Phase 2: Render Service — 10 min

⚠️ **Important:** Disable auto-deploy so GitHub Actions workflow controls when deployments happen. Otherwise Render will redeploy on *every* GitHub commit, not just fastapi/ changes.

- [ ] Go to https://dashboard.render.com
- [ ] New Web Service:
  - GitHub repo: `get-enlace/enlace-examples`
  - Branch: `main`
  - Root directory: `fastapi`
  - Build: `pip install -r requirements.txt`
  - Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
  - **Auto-deploy: OFF** ⚠️ (GitHub Actions controls deploys via deploy hook)
  - Plan: Free

- [ ] Environment Variables:
  - `DATABASE_URL` = (paste `$NEON_URL`)

- [ ] Create service
- [ ] Wait for first build to finish

## Phase 3: Deploy Hook — 5 min

- [ ] Render dashboard → Service `enlace-examples` → Settings
- [ ] Scroll to "Deploy Hooks" → Create Deploy Hook
- [ ] Name: `GitHub`
- [ ] Copy hook URL (format: `https://api.render.com/deploy/srv_...?key=...`)
- [ ] Save as `$DEPLOY_HOOK_URL`

## Phase 4: GitHub Secret — 2 min

- [ ] GitHub repo → Settings → Secrets and variables → Actions
- [ ] New secret:
  - Name: `RENDER_DEPLOY_HOOK`
  - Value: (paste `$DEPLOY_HOOK_URL`)

## Phase 5: Test Deployment — 3 min

**Test 1: Direct change trigger**
- [ ] Edit `fastapi/README.md` (add a comment)
- [ ] Commit and push to `main`
- [ ] GitHub Actions: https://github.com/get-enlace/enlace-examples/actions
- [ ] Should see `Deploy FastAPI to Render` workflow running
- [ ] Render dashboard: Should show deployment in progress
- [ ] Wait ~2 min, then open: https://enlace-examples.onrender.com/enlace

**Test 2: Auth works**
```bash
curl -X POST https://enlace-examples.onrender.com/oauth/token \
  -d "grant_type=password&username=alice@example.com&password=demo-password-123" \
  -H "Content-Type: application/x-www-form-urlencoded" | jq
```

Should return a token with `scope: "customer"`.

## Phase 6: Adapter Sync (enlace-python) — Later

When `enlace-python` repo has a deploy workflow, add this to trigger `enlace-examples` redeploy:

```yaml
# In enlace-python/.github/workflows/[deploy-workflow].yml
- name: Notify enlace-examples to redeploy
  if: success()
  run: |
    curl -X POST \
      -H "Authorization: token ${{ secrets.GITHUB_TOKEN }}" \
      -H "Accept: application/vnd.github.v3+raw" \
      https://api.github.com/repos/get-enlace/enlace-examples/dispatches \
      -d '{"event_type":"enlace-fastapi-deployed"}'
```

Once that's in place, every adapter deploy auto-triggers `enlace-examples` redeploy.

## Done! ✅

Your instance is now:
- Live at: https://enlace-examples.onrender.com/enlace
- Auto-deploying on fastapi/ changes
- Ready to sync with adapter updates (once enlace-python notifies it)

## Monitoring

**Live logs:** https://dashboard.render.com/services/enlace-examples/deployments

**Recent deploys:** Render dashboard → Service → Deployments tab

**Restart:** Render dashboard → Service → Settings → Danger Zone → Restart

---

For full details, see `DEPLOYMENT.md`.
