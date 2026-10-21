"""
SARIF v2.1.0 Exporter for GitHub Code Scanning and IDE integration.
"""
from typing import Dict, Any, List
from app.models.finding import Finding, SeverityLevel
from app.models.scan import ScanResult


def map_severity_to_sarif_level(severity: SeverityLevel) -> str:
    """Map internal DiffGuard severity to official SARIF result level."""
    if severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH]:
        return "error"
    elif severity == SeverityLevel.MEDIUM:
        return "warning"
    else:
        return "note"


def generate_sarif_report(scan_result: ScanResult) -> Dict[str, Any]:
    """
    Transforms a DiffGuard ScanResult into an OASIS-compliant SARIF v2.1.0 JSON object.
    Supported natively by GitHub Code Scanning, GitLab Security, and VS Code SARIF viewer.
    """
    rules_dict = {}
    results = []

    for f in scan_result.findings:
        # Build deduplicated rule definition in driver
        if f.rule_id not in rules_dict:
            rule_entry = {
                "id": f.rule_id,
                "name": f.title,
                "shortDescription": {
                    "text": f.title
                },
                "fullDescription": {
                    "text": f.description or f.title
                },
                "defaultConfiguration": {
                    "level": map_severity_to_sarif_level(f.severity)
                },
                "properties": {
                    "tags": ["security", f.category or "vulnerability"],
                    "precision": f.confidence.value if f.confidence else "high",
                    "problem.severity": "error" if f.severity in [SeverityLevel.CRITICAL, SeverityLevel.HIGH] else "warning"
                }
            }
            if f.remediation:
                rule_entry["help"] = {
                    "text": f"{f.description}\n\nRecommended Remediation:\n{f.remediation}"
                }
            rules_dict[f.rule_id] = rule_entry

        clean_path = f.file_path.replace("\\", "/").lstrip("/")
        level = map_severity_to_sarif_level(f.severity)

        message_text = f.description or f.title
        if f.ai_explanation and f.ai_explanation.plain_explanation:
            message_text = f"{f.title}: {f.ai_explanation.plain_explanation}"

        result_item: Dict[str, Any] = {
            "ruleId": f.rule_id,
            "level": level,
            "message": {
                "text": message_text
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": clean_path,
                            "uriBaseId": "%SRCROOT%"
                        },
                        "region": {
                            "startLine": max(1, f.line_number),
                            "endLine": max(1, f.end_line_number or f.line_number),
                            "snippet": {
                                "text": f.evidence_snippet
                            }
                        }
                    }
                }
            ]
        }

        # Include automated remediation replacement in SARIF if available
        if f.ai_explanation and f.ai_explanation.corrected_code:
            result_item["fixes"] = [
                {
                    "description": {
                        "text": f.ai_explanation.recommended_fix or "Apply AI remediation"
                    },
                    "artifactChanges": [
                        {
                            "artifactLocation": {
                                "uri": clean_path,
                                "uriBaseId": "%SRCROOT%"
                            },
                            "replacements": [
                                {
                                    "deletedRegion": {
                                        "startLine": max(1, f.line_number),
                                        "endLine": max(1, f.end_line_number or f.line_number)
                                    },
                                    "insertedContent": {
                                        "text": f.ai_explanation.corrected_code
                                    }
                                }
                            ]
                        }
                    ]
                }
            ]

        results.append(result_item)

    sarif_doc = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "DiffGuard",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/diffguard/diffguard",
                        "rules": list(rules_dict.values())
                    }
                },
                "results": results
            }
        ]
    }

    return sarif_doc
