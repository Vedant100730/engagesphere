# EngageSphere — Deployment Guide

Stack: **Render** (FastAPI backend) + **Vercel** (Next.js frontend) + **Supabase** (Postgres)

---

## Before You Start

You need accounts at:
- [render.com](https://render.com) — free tier is fine
- [vercel.com](https://vercel.com) — free tier is fine
- [developers.facebook.com](https://developers.facebook.com) — for Meta OAuth

---

## Step 1 — Push to GitHub

Both Render and Vercel deploy from a Git repo.

```bash
# From the EngageSphere root
git init          # if not already a repo
git add .
git commit -m "chore: prepare for deployment"
git remote add origin https://github.com/YOUR_USERNAME/engagesphere.git
git push -u origin main
```

> The `.gitignore` already excludes all `.env` files with real secrets.

---

## Step 2 — Deploy the Backend on Render

1. Go to **render.com → New → Web Service**
2. Connect your GitHub repo
3. Render will detect `render.yaml` automatically and pre-fill settings
4. Set **Root Directory** to `.` (the repo root — Dockerfile is at `backend/Dockerfile`)
5. Click **Create Web Service**

### Environment Variables to set in Render dashboard

Go to your service → **Environment** tab and add:

| Key | Value |
|-----|-------|
| `DATABASE_URL` | `postgresql+asyncpg://postgres:PASSWORD@db.XXXX.supabase.co:5432/postgres` |
| `GROQ_API_KEY` | your Groq key |
| `GEMINI_API_KEY` | your Gemini key |
| `OPENROUTER_API_KEY` | your OpenRouter key |
| `PINECONE_API_KEY` | your Pinecone key |
| `PINECONE_INDEX_NAME` | `engagesphere` |
| `PINECONE_ENVIRONMENT` | `us-east-1` |
| `META_APP_ID` | from Meta App dashboard |
| `META_APP_SECRET` | from Meta App dashboard |
| `FACEBOOK_PAGE_ACCESS_TOKEN` | your page token |
| `INSTAGRAM_ACCESS_TOKEN` | your IG token |
| `BACKEND_URL` | `https://engagesphere-backend.onrender.com` ← your Render URL |
| `FRONTEND_URL` | `https://engagesphere.vercel.app` ← your Vercel URL (fill after Step 3) |

After deploy, your backend will be live at:
```
https://engagesphere-backend.onrender.com
```

Test it:
```
https://engagesphere-backend.onrender.com/health
→ {"status": "ok", "service": "EngageSphere API v2"}
```

---

## Step 3 — Deploy the Frontend on Vercel

1. Go to **vercel.com → New Project → Import Git Repository**
2. Select your GitHub repo
3. Set **Root Directory** to `frontend`
4. Framework preset: **Next.js** (auto-detected)
5. Add these **Environment Variables** in the Vercel dashboard:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_URL` | `https://engagesphere-backend.onrender.com` |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://pvxmbyfndwkernerbkaf.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | your Supabase anon key |

6. Click **Deploy**

Your frontend will be live at:
```
https://engagesphere.vercel.app
```

> Go back to Render and update `FRONTEND_URL` to this Vercel URL now.

---

## Step 4 — Configure Meta App for OAuth

This is what makes Facebook/Instagram **one-click connect** work.

### 4a. Create or configure your Meta App

1. Go to [developers.facebook.com](https://developers.facebook.com) → **My Apps**
2. Select your app (App ID: `2000950423895883`) or create a new **Business** type app
3. Add **Facebook Login** product → **Settings**

### 4b. Add Valid OAuth Redirect URIs

Under **Facebook Login → Settings → Valid OAuth Redirect URIs**, add:

```
https://engagesphere-backend.onrender.com/api/oauth/facebook/callback
https://engagesphere-backend.onrender.com/api/oauth/instagram/callback
```

> These must match **exactly** — no trailing slash, exact domain.

### 4c. Required Permissions (App Review)

For **development/demo mode** (works immediately, test users only):
- No review needed — just add test users under **Roles → Test Users**

For **public launch** (any user can connect):
- Submit for App Review with these permissions:
  - `pages_show_list`
  - `pages_read_engagement`
  - `pages_manage_posts`
  - `instagram_basic`
  - `instagram_manage_comments`

---

## Step 5 — How the One-Click Connect Works

Once deployed, the user flow is fully automatic:

```
User clicks "Connect Facebook" in Settings
  → Frontend calls GET /api/oauth/facebook/start
  → Backend returns Facebook OAuth URL
  → Browser redirects to facebook.com (user logs in, clicks Allow)
  → Facebook redirects to /api/oauth/facebook/callback?code=...
  → Backend exchanges code for Page Access Token
  → Token stored in platform_connections table (Supabase)
  → Browser redirected to /settings?success=facebook
  → Settings page shows "Connected" badge
```

**No manual token input needed from the user — it's one click.**

The only thing that requires any input is the initial Meta App configuration
(Steps 4a–4b above), which is a one-time setup done by you, not your users.

---

## Step 6 — Verify Everything Works

```bash
# 1. Backend health
curl https://engagesphere-backend.onrender.com/health

# 2. OAuth start (requires auth token)
curl -H "Authorization: Bearer YOUR_JWT" \
  https://engagesphere-backend.onrender.com/api/oauth/facebook/start

# 3. Check connections after OAuth
curl -H "Authorization: Bearer YOUR_JWT" \
  https://engagesphere-backend.onrender.com/api/business/connections
```

---

## Common Issues

| Problem | Fix |
|---------|-----|
| Render build fails on `torch` | Already fixed — `requirements.txt` uses `torch+cpu` from the PyTorch CPU wheel index (~800MB vs ~2.5GB) |
| `META_APP_ID not configured` error | `META_APP_ID` env var not set in Render |
| Facebook redirects to wrong URL | Redirect URI in Meta App dashboard doesn't match `BACKEND_URL` exactly |
| CORS error from frontend | `FRONTEND_URL` in Render doesn't match the exact Vercel domain |
| `Not connected` after OAuth | Check Supabase `platform_connections` table — row should appear after OAuth |

---

## Render Free Tier Note

Render free tier **spins down after 15 minutes of inactivity**. First request after spin-down takes ~30 seconds. For a demo, hit the `/health` endpoint beforehand to wake it up. Paid tier ($7/mo) keeps it always-on.
