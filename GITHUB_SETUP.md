# Creating Didebaan as a New GitHub Repository

This project is structured as a **standalone repository** ready to be pushed to GitHub.

## Project structure (what gets committed)

```
Didebaan/
├── .env.example          # Template for environment variables (copy to .env locally)
├── .gitignore             # Ignores venv, logs, .env, db, cache, etc.
├── README.md              # Project documentation
├── GITHUB_SETUP.md        # This file
├── backend/
│   ├── config/            # Django settings, urls, wsgi
│   ├── aml/               # AML app (models, views, services, rules, ml)
│   ├── manage.py
│   └── requirements.txt
└── دیتاست-صرفا برای برخی چالش‌ها/   # Optional challenge dataset (add if needed)
```

**Not committed** (see `.gitignore`): `venv/`, `backend/logs/*.log`, `.env`, `db.sqlite3`, `__pycache__/`, etc.

---

## Step 1: Initialize Git in Didebaan (if not already)

From your machine, in the Didebaan folder:

```bash
cd /Users/massoudshemirani/MyProjects/Didebaan
git init
git add .
git status   # Review: venv, .env, logs should be ignored
git commit -m "Initial commit: Didebaan AML system (Django + DRF)"
```

---

## Step 2: Create a new repository on GitHub

1. Go to [GitHub](https://github.com) → **New repository**.
2. **Repository name:** e.g. `Didebaan` or `didebaan-aml`.
3. **Description:** e.g. `AML (Anti-Money Laundering) system – transaction monitoring, risk scoring, alerts, regulatory reports (RegMeet challenge).`
4. Choose **Public** (or Private).
5. **Do not** add a README, .gitignore, or license here (they already exist in your project).
6. Click **Create repository**.

---

## Step 3: Push your project to GitHub

GitHub will show commands; use these (replace `YOUR_USERNAME` and `REPO_NAME` with your values):

```bash
cd /Users/massoudshemirani/MyProjects/Didebaan
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

If you use SSH:

```bash
git remote add origin git@github.com:YOUR_USERNAME/REPO_NAME.git
git branch -M main
git push -u origin main
```

---

## Step 4 (optional): Add LICENSE

If you want a license file:

- Create `LICENSE` in the project root (e.g. MIT, Apache 2.0).
- Then: `git add LICENSE` and `git commit -m "Add LICENSE"` and `git push`.

---

## Summary

| Action              | Location / command                          |
|---------------------|---------------------------------------------|
| Git repo            | Initialized inside `Didebaan/` (this folder) |
| Ignore venv/logs/env| `.gitignore`                                |
| Env template        | `.env.example` → copy to `.env` locally     |
| Create repo         | GitHub → New repository                     |
| Push                | `git remote add origin ...` then `git push`  |

After pushing, anyone can clone with:

```bash
git clone https://github.com/YOUR_USERNAME/REPO_NAME.git
cd REPO_NAME
```

Then follow the **نصب و راه‌اندازی** section in `README.md`.
