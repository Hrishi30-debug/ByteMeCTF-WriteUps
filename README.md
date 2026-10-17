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

**Example:**
```
Writeups/
└── suyog/
    └── OSINT/
        ├── stalker_0.md
        └── resources/
            ├── stalker0.jpeg
            ├── stalker0_sol1.png
            └── stalker0_sol2.png
```

---

## ✍️ How to Contribute

### 1. Clone the repo
```bash
git clone git@github.com:suyog-jadhav/ByteMeCTF-WriteUps.git
cd ByteMeCTF-WriteUps
```

### 2. Create your folder (first time only)
```bash
mkdir -p Writeups/yourname/Web/resources
```

### 3. Write your writeup
Create a Markdown file: `Writeups/<your-name>/<category>/<challenge-name>.md`

Use this template:

```md
# Challenge Name (Category, Difficulty)

**Author:** Your Name
**Category:** Web / OSINT / Crypto / ...
**Difficulty:** Easy / Medium / Hard

## Challenge Description
> Paste the challenge description here.

## Summary
Brief overview of the approach.

## Flag
​```
FLAG{...}
​```

## Step 1 — ...
...

## Tools Used
- ...
```

### 4. Add screenshots / resources
Place them in a `resources/` subfolder next to your `.md` file and reference them with a relative path:
```md
![Description](resources/screenshot.png)
```

### 5. Commit and push
```bash
git add .
git commit -m "feat: add <challenge-name> writeup by <your-name>"
git push origin main
```

> **Tip:** If you get a conflict (someone else pushed first), run `git pull origin main` first, then push again.

---

## ✅ Writeup Checklist

- [ ] File is under `Writeups/<your-name>/<category>/`
- [ ] Challenge name uses underscores (e.g. `stalker_0.md`)
- [ ] All images/resources are in a `resources/` subfolder
- [ ] Flag is clearly shown in a code block
- [ ] Steps are numbered and explained

---

## 👥 Authors

| Name | GitHub |
|---|---|
| Suyog Jadhav | [@suyog-jadhav](https://github.com/suyog-jadhav) |

*Add your row here when you submit your first writeup!*
