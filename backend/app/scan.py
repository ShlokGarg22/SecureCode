import argparse
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional

from app.core.config import settings
from app.models.finding import SeverityLevel, FindingStatus
from app.models.scan import ScanResult, SeveritySummary
from app.engine.semgrep import SemgrepRunner
from app.engine.gitleaks import GitleaksRunner, normalize_gitleaks_findings
from app.engine.normalizer import normalize_semgrep_findings
from app.ai.explainer import explainer_service
from app.engine.patch_generator import generate_unified_patch
from app.engine.sarif_exporter import generate_sarif_report

SEVERITY_ORDER = {
    SeverityLevel.CRITICAL: 5,
    SeverityLevel.HIGH: 4,
    SeverityLevel.MEDIUM: 3,
    SeverityLevel.LOW: 2,
    SeverityLevel.INFORMATIONAL: 1
}


def format_github_step_summary(result: ScanResult) -> str:
    """Format an attractive Markdown dashboard for GitHub Actions $GITHUB_STEP_SUMMARY."""
    lines = [
        f"## 🛡️ SecureCode Review: {result.project_name}",
        "",
        f"- **Scan ID**: `{result.scan_id}`",
        f"- **Scanners**: {', '.join(result.scanners_used) or 'None'}",
        f"- **Total Findings**: **{result.findings_count}**",
        "",
        "### 📊 Severity Breakdown",
        "",
        "| Critical 🔴 | High 🟠 | Medium 🟡 | Low 🔵 | Info ⚪ |",
        "| :---: | :---: | :---: | :---: | :---: |",
        f"| {result.severity_breakdown.critical} | {result.severity_breakdown.high} | {result.severity_breakdown.medium} | {result.severity_breakdown.low} | {result.severity_breakdown.informational} |",
        "",
    ]

    if not result.findings:
        lines.append("🎉 **No security vulnerabilities detected! Clean code.**\n")
        return "\n".join(lines)

    lines.append("> [!TIP]")
    lines.append("> **Automated Fix Patch Available**: A Git unified remediation patch was generated for this commit.")
    lines.append("> Download the `remediation-patch` artifact from this workflow run and apply all fixes instantly:")
    lines.append("> ```bash")
    lines.append("> git apply remediation.patch")
    lines.append("> ```\n")

    lines.append("### 🔍 Security Findings & AI Remediations\n")
    for idx, f in enumerate(result.findings[:25], 1):
        icon = "🔴" if f.severity.value in ["critical", "high"] else "🟡" if f.severity.value == "medium" else "🔵"
        lines.append(f"<details>")
        lines.append(f"<summary><b>{idx}. {icon} [{f.severity.value.upper()}] {f.title}</b> — <code>{f.file_path}:{f.line_number}</code></summary>\n")
        lines.append(f"- **File**: `{f.file_path}` (Line {f.line_number})")
        lines.append(f"- **Rule ID**: `{f.rule_id}`")
        if f.ai_explanation:
            if f.ai_explanation.plain_explanation:
                lines.append(f"- **Why it matters**: {f.ai_explanation.plain_explanation}")
            if f.ai_explanation.attack_scenario:
                lines.append(f"- **Attack Scenario**: {f.ai_explanation.attack_scenario}")
            if f.ai_explanation.recommended_fix:
                lines.append(f"- **Recommended Fix**: {f.ai_explanation.recommended_fix}")
            if f.ai_explanation.diff_unified:
                lines.append("\n**Suggested Remediation Diff:**\n")
                lines.append("```diff")
                lines.append(f.ai_explanation.diff_unified.strip())
                lines.append("```\n")
        elif f.remediation:
            lines.append(f"- **Fix**: {f.remediation}")
        lines.append("</details>\n")

    return "\n".join(lines)


def run_cli_scan(
    scan_path: Path,
    rule_mode: str = "bundled",
    enable_ai: bool = False,
    output_file: Optional[Path] = None,
    patch_file: Optional[Path] = None,
    sarif_file: Optional[Path] = None,
    fail_on: str = "high"
) -> int:
    """
    Direct CLI entry point for local scans and GitHub Actions CI.
    Scans a local directory without requiring ZIP upload or web server.
    """
    if not scan_path.exists():
        print(f"Error: Path '{scan_path}' does not exist.", file=sys.stderr)
        return 2

    print(f"[*] DiffGuard Scanning: {scan_path.resolve()}")
    print(f"[*] Rule Mode: {rule_mode}")

    scanners_used = []
    all_findings = []

    semgrep_runner = SemgrepRunner()
    if semgrep_runner.is_available():
        scanners_used.append("semgrep")
        print("[+] Running Semgrep static analysis (excluding 3rd-party dependencies)...")
        try:
            raw_data = semgrep_runner.run_scan(target_dir=scan_path, rule_mode=rule_mode)
            findings = normalize_semgrep_findings(raw_data, base_dir=scan_path)
            all_findings.extend(findings)
            print(f"    Semgrep reported {len(findings)} finding(s).")
        except Exception as e:
            print(f"    [!] Semgrep error: {e}", file=sys.stderr)
    else:
        print("[!] Semgrep is not available on PATH.")

    gitleaks_runner = GitleaksRunner()
    if gitleaks_runner.is_available():
        scanners_used.append("gitleaks")
        print("[+] Running Gitleaks secret detection...")
        try:
            raw_leaks = gitleaks_runner.run_scan(target_dir=scan_path)
            findings = normalize_gitleaks_findings(raw_leaks, base_dir=scan_path)
            all_findings.extend(findings)
            print(f"    Gitleaks reported {len(findings)} secret leak(s).")
        except Exception as e:
            print(f"    [!] Gitleaks error: {e}", file=sys.stderr)

    if enable_ai:
        print("[+] Generating security explanations & remediation diffs...")
        for f in all_findings:
            f.ai_explanation = explainer_service.explain_finding(f)

    # Count severities
    summary = SeveritySummary()
    for f in all_findings:
        if f.severity == SeverityLevel.CRITICAL:
            summary.critical += 1
        elif f.severity == SeverityLevel.HIGH:
            summary.high += 1
        elif f.severity == SeverityLevel.MEDIUM:
            summary.medium += 1
        elif f.severity == SeverityLevel.LOW:
            summary.low += 1
        elif f.severity == SeverityLevel.INFORMATIONAL:
            summary.informational += 1

    result = ScanResult(
        scan_id=f"CLI-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        project_name=scan_path.name,
        created_at=datetime.utcnow(),
        duration_seconds=0.0,
        scanners_used=scanners_used,
        rule_mode=rule_mode,
        files_scanned=1,
        findings_count=len(all_findings),
        severity_breakdown=summary,
        findings=all_findings
    )

    # Write JSON output if requested
    if output_file:
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(result.model_dump(mode="json"), indent=2), encoding="utf-8")
        print(f"[+] JSON results saved to: {output_file}")

    # Write Git patch if requested
    if patch_file:
        patch_file.parent.mkdir(parents=True, exist_ok=True)
        patch_text = generate_unified_patch(all_findings, scan_id=result.scan_id)
        patch_file.write_text(patch_text, encoding="utf-8")
        print(f"[+] Unified remediation patch saved to: {patch_file}")

    # Write SARIF report if requested
    if sarif_file:
        sarif_file.parent.mkdir(parents=True, exist_ok=True)
        sarif_json = generate_sarif_report(result)
        sarif_file.write_text(json.dumps(sarif_json, indent=2), encoding="utf-8")
        print(f"[+] SARIF v2.1.0 report saved to: {sarif_file}")

    # Write GitHub Step Summary if running in GitHub Actions
    gh_summary_path = os.getenv("GITHUB_STEP_SUMMARY")
    if gh_summary_path:
        try:
            summary_content = format_github_step_summary(result)
            with open(gh_summary_path, "a", encoding="utf-8") as f:
                f.write(summary_content + "\n")
            print("[+] Appended results to GitHub Actions Step Summary.")
        except Exception as e:
            print(f"[!] Could not write to GITHUB_STEP_SUMMARY: {e}", file=sys.stderr)

    # Print human-readable summary
    print("\n" + "=" * 50)
    print(f"DiffGuard Scan Summary for: {scan_path.name}")
    print("=" * 50)
    print(f"Critical:      {summary.critical}")
    print(f"High:          {summary.high}")
    print(f"Medium:        {summary.medium}")
    print(f"Low:           {summary.low}")
    print(f"Informational: {summary.informational}")
    print(f"Total:         {len(all_findings)}")
    print("=" * 50)

    # Evaluate failure threshold for CI
    if fail_on.lower() == "none":
        print("\n[+] DiffGuard scan completed (fail-on=none).")
        return 0

    threshold_level = SeverityLevel(fail_on.lower()) if fail_on.lower() in [s.value for s in SeverityLevel] else SeverityLevel.HIGH
    min_weight = SEVERITY_ORDER[threshold_level]

    violating_findings = [f for f in all_findings if SEVERITY_ORDER[f.severity] >= min_weight]
    if violating_findings:
        print(f"\n[!] Policy failure: {len(violating_findings)} finding(s) met or exceeded severity threshold '{threshold_level.value}'.")
        return 1

    print("\n[+] DiffGuard scan passed policy threshold.")
    return 0


def main():
    parser = argparse.ArgumentParser(description="DiffGuard Security Scanner CLI")
    parser.add_argument("--path", "-p", type=Path, default=Path("."), help="Path to scan")
    parser.add_argument("--rule-mode", choices=["bundled", "online", "hybrid"], default="bundled", help="Rule set mode")
    parser.add_argument("--enable-ai", action="store_true", help="Enable AI explanations")
    parser.add_argument("--output", "-o", type=Path, default=None, help="Output JSON report file")
    parser.add_argument("--patch-output", "--patch", type=Path, default=None, help="Output unified Git remediation patch file (.patch)")
    parser.add_argument("--sarif-output", "--sarif", type=Path, default=None, help="Output SARIF v2.1.0 report file")
    parser.add_argument("--fail-on", choices=["critical", "high", "medium", "low", "none"], default="high", help="Exit with error on severity")

    args = parser.parse_args()
    exit_code = run_cli_scan(
        scan_path=args.path,
        rule_mode=args.rule_mode,
        enable_ai=args.enable_ai,
        output_file=args.output,
        patch_file=args.patch_output,
        sarif_file=args.sarif_output,
        fail_on=args.fail_on
    )
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
