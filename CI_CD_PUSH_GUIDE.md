# 🛡️ SecureCode: Zero-Hosting "On-Push" CI/CD Guide

SecureCode runs automated security reviews **every time code is pushed** to GitHub — with **$0 hosting cost**, **zero server maintenance**, and **zero code changes** to your application.

---

## ⚡ What Happens When a Developer Pushes Code?

```
Developer runs: git push
        │
        ▼
GitHub Cloud Server spins up (Free tier)
        │
        ▼
Runs SecureCode Engine:
  ├── 1. Excludes 3rd-party noise (node_modules, venv, .git)
  ├── 2. Scans for SAST bugs (Semgrep) & leaked credentials (Gitleaks)
  ├── 3. Generates AI explanations & unified diff fixes
  ├── 4. Exports remediation.patch for one-command fixes
  └── 5. Generates OASIS SARIF v2.1.0 report
        │
        ▼
Developer sees 4 immediate results:
  1. Commit Status: 🟢 Green Checkmark (Clean) or 🔴 Red X (Action Needed)
  2. GitHub Security Tab: Interactive alerts with line-by-line annotations
  3. Action Run Summary: Full Markdown dashboard with expandable diffs
  4. Downloadable Patch: `remediation.patch` to fix all issues with `git apply`
```

---

## 🚀 How to Enable SecureCode in Any Repository (30 Seconds)

You only need **1 file** in your repository.

### Step 1: Add the Workflow File
In your repository, create the file:
`.github/workflows/securecode.yml`

Paste the following configuration:

```yaml
name: SecureCode CI Security & Remediation

on:
  push:
    branches: [ "**" ]   # Runs on every push to any branch
  pull_request:
    branches: [ "**" ]   # Runs whenever a PR is created or updated
  workflow_dispatch:     # Allows manual trigger button in GitHub UI

permissions:
  contents: read
  security-events: write  # Uploads alerts to the GitHub Security tab
  actions: read
  pull-requests: write    # Comments diffs on Pull Requests

jobs:
  security-scan:
    name: Run SecureCode Security Analysis
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run SecureCode Scanner
        uses: ./  # Or replace with <your-org>/SecureCode@v1
        with:
          path: "."
          fail-on: "high"         # Fail build on 'high' or 'critical' (options: critical, high, medium, low, none)
          enable-ai: "true"       # Generate remediation diffs
          patch-output: "remediation.patch"
          sarif-output: "securecode.sarif"
          groq-api-key: ${{ secrets.GROQ_API_KEY }}  # Optional: high-speed AI diffs

      - name: Upload SARIF to GitHub Security Tab
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: "securecode.sarif"
        continue-on-error: true

      - name: Archive Remediation Patch
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: remediation-patch
          path: remediation.patch
          if-no-files-found: ignore

      - name: Comment Remediation Diffs on Pull Request
        if: github.event_name == 'pull_request' && always()
        uses: actions/github-script@v7
        continue-on-error: true
        with:
          script: |
            const fs = require('fs');
            const summaryFile = process.env.GITHUB_STEP_SUMMARY;
            if (summaryFile && fs.existsSync(summaryFile)) {
              const body = fs.readFileSync(summaryFile, 'utf8');
              if (body && body.trim().length > 0) {
                await github.rest.issues.createComment({
                  issue_number: context.issue.number,
                  owner: context.repo.owner,
                  repo: context.repo.repo,
                  body: body
                });
              }
            }
```

---

## 🛠️ Step 2: (Optional) Add an AI API Key

SecureCode includes a **100% offline, deterministic remediation engine** that works with zero API keys. 

If you want ultra-fast dynamic remediation diffs powered by Llama 3.3:
1. Go to your repository on GitHub.
2. Click **Settings** $\rightarrow$ **Secrets and variables** $\rightarrow$ **Actions**.
3. Click **New repository secret**.
4. Name: `GROQ_API_KEY`
5. Value: Your Groq API key.

---

## 🧑‍💻 How Developers Fix Vulnerabilities in 1 Command

When a push triggers a security finding:

1. Click on the **Actions** tab of the workflow run (or view the Pull Request comment).
2. Download the **`remediation-patch`** artifact.
3. In your local terminal, apply the patch:
   ```bash
   git apply remediation.patch
   ```
4. Review the changes with `git diff`, commit, and push:
   ```bash
   git commit -am "Apply SecureCode automated fixes"
   git push
   ```
5. Your commit status turns **Green 🟢 (Passed)**.
