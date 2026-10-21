"""
Unified Git patch generator for automated code remediation.
"""
import difflib
from typing import List, Optional
from app.models.finding import Finding


def generate_unified_patch(findings: List[Finding], scan_id: Optional[str] = "DIFFGUARD") -> str:
    """
    Generates a consolidated, standard Git unified patch from a list of security findings.
    Can be directly applied using `git apply <patch_file>`.
    """
    patch_chunks = []

    header = [
        f"# SecureCode Automated Remediation Patch",
        f"# Scan ID: {scan_id}",
        f"# Total Findings: {len(findings)}",
        f"# Apply this patch with: git apply <patch_file>",
        "",
    ]
    patch_chunks.append("\n".join(header))

    by_file = {}
    for f in findings:
        if not f.ai_explanation:
            continue
        by_file.setdefault(f.file_path, []).append(f)

    for file_path, file_findings in by_file.items():
        clean_path = file_path.replace("\\", "/").lstrip("/")

        for f in file_findings:
            exp = f.ai_explanation
            if not exp:
                continue

            orig = (exp.original_code or f.evidence_snippet or "").strip()
            fixed = (exp.corrected_code or "").strip()

            # Prefer exact unified diff generation from original and corrected snippets
            if orig and fixed and orig != fixed:
                orig_lines = [line + "\n" for line in orig.splitlines()]
                fixed_lines = [line + "\n" for line in fixed.splitlines()]

                diff_lines = list(difflib.unified_diff(
                    orig_lines,
                    fixed_lines,
                    fromfile=f"a/{clean_path}",
                    tofile=f"b/{clean_path}",
                    n=2
                ))
                if diff_lines:
                    patch_chunks.append("".join(diff_lines))
                    continue

            # Fallback to precomputed diff_unified
            if exp.diff_unified and exp.diff_unified.strip():
                diff_text = exp.diff_unified.strip()
                if not diff_text.startswith("---"):
                    diff_text = f"--- a/{clean_path}\n+++ b/{clean_path}\n{diff_text}\n"
                patch_chunks.append(diff_text)

    return "\n".join(patch_chunks).strip() + "\n"
