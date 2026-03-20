# How to Push to GitHub Safely

## The Rule
- `.env` = your local machine ONLY. It is in `.gitignore`. It never goes to GitHub.
- `.env.example` = what you commit. It has fake placeholder values, no real secrets.
- GitHub Secrets = where real keys live for CI/CD and production.

---

## Step 1 — Make sure .env is not tracked

```bash
# Inside WSL2, inside your project folder:
git status

# If you see .env in the list, run this FIRST:
git rm --cached .env

# You should never see .env in git status after this.
```

---

## Step 2 — Initialise git and push

```bash
cd complaint-system

git init
git add .
git status        # ← look through this. You should NOT see .env

git commit -m "feat: Sprint 1 — ingest API + Twilio channel"

# Create a new repo on github.com (call it complaint-system)
# Then connect it:
git remote add origin https://github.com/YOUR_USERNAME/complaint-system.git
git branch -M main
git push -u origin main
```

---

## Step 3 — Add secrets to GitHub (one-time setup)

Go to your repo on GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

Add each of these:

| Secret Name        | Value                          |
|--------------------|--------------------------------|
| POSTGRES_PASSWORD  | (whatever you set in .env)     |
| REDIS_PASSWORD     | (whatever you set in .env)     |
| ANTHROPIC_API_KEY  | sk-ant-...                     |
| TWILIO_SID         | ACxxxxxxxx...                  |
| TWILIO_AUTH_TOKEN  | your token                     |
| TWILIO_NUMBER      | whatsapp:+14155238886          |

These are encrypted by GitHub. Nobody can read them — not even you after saving.
The CI workflow reads them as ${{ secrets.NAME }} automatically.

---

## Step 4 — New developer joins the team

They clone the repo:
```bash
git clone https://github.com/YOUR_USERNAME/complaint-system.git
cd complaint-system

# They copy the template and fill in their own values
cp .env.example .env
# Edit .env with real keys (you share keys privately via 1Password / WhatsApp DM — never email)

docker compose up -d
```

---

## What goes where — summary

| Location           | Contains              | On GitHub? |
|--------------------|-----------------------|------------|
| `.env`             | Real keys             | ❌ Never   |
| `.env.example`     | Fake placeholder text | ✅ Yes     |
| GitHub Secrets     | Real keys for CI/CD   | ✅ Encrypted |
| Code files         | No keys ever          | ✅ Yes     |

---

## Emergency: if you accidentally committed .env

```bash
# 1. Remove it from git history (before anyone pulls)
git rm --cached .env
git commit -m "fix: remove accidentally committed .env"
git push

# 2. Rotate ALL keys immediately — assume they are compromised
#    - Anthropic dashboard → regenerate API key
#    - Twilio console → regenerate auth token
#    - Change DB passwords

# 3. Add .env to .gitignore if it wasn't already
```
