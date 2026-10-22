#!/usr/bin/env python3
"""
Groq Model Discovery and Diagnostic Tool for SecureCode.
Lists all models available to your Groq API key, tests inference latency,
and validates JSON remediation output for DiffGuard/SecureCode.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure UTF-8 output on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Load environment from .env if present
try:
    from dotenv import load_dotenv
    root_dir = Path(__file__).resolve().parent
    if (root_dir / "backend" / ".env").exists():
        load_dotenv(root_dir / "backend" / ".env", override=True)
    if (root_dir / ".env").exists():
        load_dotenv(root_dir / ".env", override=False)
except ImportError:
    pass

try:
    from groq import Groq
except ImportError:
    print("[!] 'groq' package is not installed.")
    print("    Run: pip install groq")
    sys.exit(1)


def get_api_key(arg_key: str = None) -> str:
    """Retrieve Groq API key from args, env, or user input."""
    if arg_key:
        return arg_key.strip()
    
    env_key = os.getenv("GROQ_API_KEY", "").strip()
    if env_key:
        return env_key
    
    print("\n" + "=" * 60)
    print("🔑 Groq API Key Required")
    print("=" * 60)
    print("Get your free key at: https://console.groq.com/keys")
    try:
        user_input = input("Enter your GROQ_API_KEY (or press Ctrl+C to exit): ").strip()
        if user_input:
            return user_input
    except (KeyboardInterrupt, EOFError):
        print("\nAborted.")
        sys.exit(0)
    
    print("[!] No API key provided.")
    sys.exit(1)


def list_and_test_groq_models(api_key: str, test_inference: bool = True):
    print(f"\n[*] Authenticating with Groq API (key: {api_key[:6]}...{api_key[-4:]})...")
    client = Groq(api_key=api_key)

    try:
        models_response = client.models.list()
        all_models = models_response.data
    except Exception as e:
        print(f"\n❌ Failed to connect to Groq: {e}", file=sys.stderr)
        return

    print(f"✅ Successfully authenticated! Found {len(all_models)} model(s) available on your account.\n")

    # Sort models by ID
    chat_models = []
    other_models = []

    for m in all_models:
        model_id = m.id
        # Categorize
        if any(kw in model_id.lower() for kw in ["whisper", "distil-whisper", "tts", "embedding"]):
            other_models.append(m)
        else:
            chat_models.append(m)

    chat_models.sort(key=lambda x: x.id)

    print("=" * 75)
    print(f"{'MODEL ID':<35} | {'OWNER':<12} | {'ACTIVE':<8} | {'CONTEXT'}")
    print("=" * 75)

    for m in chat_models:
        owned_by = getattr(m, "owned_by", "groq") or "groq"
        active = getattr(m, "active", True)
        ctx = getattr(m, "context_window", "N/A")
        print(f"{m.id:<35} | {owned_by:<12} | {str(active):<8} | {ctx}")

    print("=" * 75)

    if not test_inference:
        return

    print("\n[*] Testing live chat completion & JSON security analysis on candidate models...\n")
    
    test_prompt = (
        "You are a code security auditor. Analyze this Python snippet: 'eval(user_input)'. "
        "Return valid JSON with keys: plain_explanation, recommended_fix."
    )

    test_results = []
    
    # Priority list of models to test
    priority_order = [
        "llama-3.1-8b-instant",
        "llama-3.3-70b-versatile",
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b",
        "mixtral-8x7b-32768",
        "gemma2-9b-it"
    ]

    # Models present in account to test
    available_ids = {m.id for m in chat_models}
    to_test = [pid for pid in priority_order if pid in available_ids]
    # Add any remaining chat models (up to 3)
    for m in chat_models:
        if m.id not in to_test and len(to_test) < 8:
            to_test.append(m.id)

    for model_id in to_test:
        print(f"  👉 Testing '{model_id}'...", end=" ", flush=True)
        t0 = time.time()
        try:
            resp = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Return valid JSON."},
                    {"role": "user", "content": test_prompt}
                ],
                model=model_id,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            elapsed_ms = (time.time() - t0) * 1000
            content = resp.choices[0].message.content
            # Validate JSON
            data = json.loads(content)
            has_fix = "recommended_fix" in data or "plain_explanation" in data
            if has_fix:
                print(f"✅ PASSED ({elapsed_ms:.0f}ms)")
                test_results.append((model_id, True, elapsed_ms, "OK"))
            else:
                print(f"⚠️ Responded in {elapsed_ms:.0f}ms but JSON keys differed.")
                test_results.append((model_id, True, elapsed_ms, "Keys differed"))
        except Exception as e:
            err_msg = str(e)
            if "rate_limit" in err_msg.lower():
                status = "Rate limited (TPM/RPM)"
            elif "not found" in err_msg.lower():
                status = "Model not found / restricted"
            else:
                status = err_msg.splitlines()[0][:45]
            print(f"❌ FAILED ({status})")
            test_results.append((model_id, False, 0, status))

    print("\n" + "=" * 75)
    print("📊 Security Analysis Test Results")
    print("=" * 75)
    
    working_models = [r for r in test_results if r[1]]

    if working_models:
        # Sort by speed
        working_models.sort(key=lambda x: x[2])
        best_model = working_models[0][0]
        
        print(f"🏆 Best Performing Model for SecureCode: '{best_model}'")
        print("\nAll Verified Working Models:")
        for mid, ok, ms, msg in working_models:
            print(f"  - {mid:<30} (~{ms:.0f}ms latency)")

        print("\n" + "=" * 75)
        print("💡 How to configure SecureCode to use this model:")
        print("=" * 75)
        print("1. In your local '.env' file:")
        print(f"   GROQ_API_KEY={api_key}")
        print(f"   GROQ_MODEL={best_model}")
        print("\n2. In your GitHub Actions workflow (.github/workflows/securecode.yml):")
        print("   - name: Run SecureCode Security Analysis")
        print("     uses: ShlokGarg22/SecureCode@main")
        print("     with:")
        print('       fail-on: "high"')
        print('       enable-ai: "true"')
        print("       groq-api-key: ${{ secrets.GROQ_API_KEY }}")
        print(f'       groq-model: "{best_model}"')
        print("=" * 75)
    else:
        print("❌ No models passed chat completions with this API key.")
        print("Please check your Groq account status and tier at: https://console.groq.com")


def main():
    parser = argparse.ArgumentParser(description="Check available Groq models for SecureCode")
    parser.add_argument("--key", "-k", help="Groq API key (optional, falls back to env GROQ_API_KEY)")
    parser.add_argument("--no-test", action="store_true", help="List models only without running test prompts")
    args = parser.parse_args()

    api_key = get_api_key(args.key)
    list_and_test_groq_models(api_key, test_inference=not args.no_test)


if __name__ == "__main__":
    main()
