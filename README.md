# ByteMeCTF — WriteUps

A collaborative collection of CTF writeups by the OWASP PCCOE team.

---

## 📁 Repository Structure

```
Writeups/
└── <your-name>/
    └── <category>/
        ├── <challenge-name>.md
        └── resources/
            └── (screenshots, images, files used in the writeup)
```

**Categories:** `OSINT` · `Web` · `Crypto` · `Pwn` · `Rev` · `Forensics` · `Misc`

---

## 🚀 Quick Start (First Time Setup)

### Prerequisites
- Git installed on your machine
- A GitHub account
- SSH key added to GitHub **or** use HTTPS

### 1. Get access
Ask **@suyog-jadhav** to add you as a collaborator on the repo.  
You'll get an email invite — accept it.

### 2. Clone the repo
```bash
git clone git@github.com:suyog-jadhav/ByteMeCTF-WriteUps.git
cd ByteMeCTF-WriteUps
```
> Using HTTPS instead? Replace the URL with:
> `https://github.com/suyog-jadhav/ByteMeCTF-WriteUps.git`

---

## ✍️ Adding Your Writeup (Every Time)

### Step 1 — Pull the latest changes
Always start from an up-to-date `main`:
```bash
git checkout main
git pull origin main
```

### Step 2 — Create your branch
Name your branch `<yourname>/<challenge-name>`:
```bash
git checkout -b alice/web-sqli-0
```

### Step 3 — Create your folder structure
```bash
mkdir -p Writeups/alice/Web/resources
```

Your writeup lives here:
```
Writeups/
└── alice/
    └── Web/
        ├── sqli_0.md         ← your writeup
        └── resources/
            └── screenshot.png
```

### Step 4 — Write your writeup
Create `Writeups/<yourname>/<category>/<challenge-name>.md` using this template:

```md
# Challenge Name (Category, Difficulty)

**Author:** Your Name
**Category:** Web / OSINT / Crypto / ...
**Difficulty:** Easy / Medium / Hard

## Challenge Description
> Paste the challenge description here.

## Summary
Brief overview of the approach used to solve the challenge.

## Flag
```
FLAG{...}
```

## Step 1 — ...

Explain what you did.

## Step 2 — ...

Add screenshots where helpful:
![Description](resources/screenshot.png)

## Tools Used
- Tool 1
- Tool 2

## Timeline

| Step | Action | Result |
|---|---|---|
| 1 | ... | ... |
```

### Step 5 — Add your screenshots / files
Place all images and supporting files inside `resources/`:
```bash
cp ~/Downloads/screenshot.png Writeups/alice/Web/resources/
```

Reference them in your markdown with a **relative path**:
```md
![Login page](resources/screenshot.png)
```

### Step 6 — Commit your work
```bash
git add .
git commit -m "feat: add sqli_0 writeup by alice"
```

Use a clear commit message:
- ✅ `feat: add sqli_0 writeup by alice`
- ✅ `feat: add stalker_0 OSINT writeup`
- ❌ `added stuff`
- ❌ `writeup`

### Step 7 — Push your branch
```bash
git push origin alice/web-sqli-0
```

### Step 8 — Open a Pull Request
1. Go to **[github.com/suyog-jadhav/ByteMeCTF-WriteUps](https://github.com/suyog-jadhav/ByteMeCTF-WriteUps)**
2. You'll see a banner: **"Compare & pull request"** — click it
3. Set:
   - **base:** `main`
   - **compare:** `alice/web-sqli-0`
4. Title: `[Web] SQLi 0 — writeup by Alice`
5. Click **Create pull request**

Suyog will review and merge it. ✅

---

## ✅ Writeup Checklist

Before opening a PR, make sure:

- [ ] Your folder is `Writeups/<your-name>/<category>/`
- [ ] Challenge filename uses underscores (e.g. `sqli_0.md`, `stalker_0.md`)
- [ ] All images are inside a `resources/` subfolder
- [ ] Images are referenced with relative paths (`resources/img.png`)
- [ ] The flag is shown in a code block
- [ ] Steps are numbered and clearly explained
- [ ] Commit message is descriptive

---

## ⚠️ Rules

- **Never push directly to `main`** — always use a branch + PR
- **Only edit files inside your own folder** (`Writeups/<your-name>/`)
- **Don't commit sensitive data** — no private keys, credentials, or personal info beyond what's in the challenge
- Keep the `referenc/` folder out of your commits (it's in `.gitignore` for a reason)

---

## 🆘 Common Issues

**Conflict when pushing?**
```bash
git checkout main
git pull origin main
git checkout alice/web-sqli-0
git rebase main
git push origin alice/web-sqli-0 --force-with-lease
```

**Wrong branch? Start over cleanly:**
```bash
git checkout main
git pull origin main
git checkout -b alice/correct-branch-name
```

**Forgot to pull before starting?**
```bash
git fetch origin
git rebase origin/main
```

---

## 👥 Authors

| Name | GitHub |
|---|---|
| Suyog Jadhav | [@suyog-jadhav](https://github.com/suyog-jadhav) |

*Add your row here when you submit your first writeup PR!*
