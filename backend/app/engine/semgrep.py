import json
import logging
import subprocess
import shutil
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)


class SemgrepRunner:
    def __init__(self, binary_name: Optional[str] = None):
        self.binary = self._resolve_binary(binary_name or settings.semgrep_binary)

    def _resolve_binary(self, binary_name: str) -> str:
        # 1. Check system PATH
        found = shutil.which(binary_name)
        if found:
            return found

        # 2. Check Python environment Scripts directory (common in Windows & venvs)
        py_dir = Path(sys.executable).parent
        candidates = [
            py_dir / "Scripts" / "semgrep.exe",
            py_dir / "Scripts" / "semgrep",
            py_dir / "semgrep.exe",
            py_dir / "semgrep",
        ]
        for c in candidates:
            if c.exists():
                return str(c)

        return binary_name

    def is_available(self) -> bool:
        """Check if Semgrep is installed and accessible."""
        if Path(self.binary).is_file():
            return True
        return shutil.which(self.binary) is not None

    def run_scan(
        self,
        target_dir: Path,
        rule_mode: str = "bundled",
        custom_rule_pack: Optional[str] = None,
        timeout: Optional[int] = None,
        excludes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Executes Semgrep safely using a subprocess argument list.
        """
        if not self.is_available():
            raise RuntimeError(
                f"Semgrep binary '{self.binary}' is not available on PATH. "
                "Ensure semgrep is installed via pip (pip install semgrep) or run via Docker."
            )

        timeout_sec = timeout or settings.scanner_timeout_seconds
        cmd: List[str] = [
            self.binary,
            "scan",
            "--json",
            "--quiet",
            "--no-git-ignore",  # Scan all files in target directory
        ]

        # Add exclusion patterns to skip third-party directories
        active_exclusions = excludes if excludes is not None else settings.default_exclusions
        for exc in active_exclusions:
            cmd.extend(["--exclude", exc])

        # Determine rule configurations safely
        if rule_mode == "bundled":
            cmd.extend(["--config", str(settings.rules_dir)])
        elif rule_mode == "online":
            online_pack = custom_rule_pack or "p/security-audit"
            cmd.extend(["--config", online_pack])
        elif rule_mode == "hybrid":
            cmd.extend(["--config", str(settings.rules_dir)])
            online_pack = custom_rule_pack or "p/security-audit"
            cmd.extend(["--config", online_pack])
        else:
            cmd.extend(["--config", str(settings.rules_dir)])

        # Target directory to scan
        cmd.append(str(target_dir))

        logger.info(f"Executing Semgrep command: {' '.join(cmd)}")

        extra_kwargs = {}
        if sys.platform == "win32":
            extra_kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                text=True,
                timeout=timeout_sec,
                shell=False,
                check=False,
                **extra_kwargs
            )

            stdout = result.stdout.strip()
            stderr = result.stderr.strip()

            if not stdout:
                if result.returncode != 0:
                    logger.error(f"Semgrep failed with return code {result.returncode}: {stderr}")
                    raise RuntimeError(f"Semgrep execution failed: {stderr}")
                return {"results": [], "errors": []}

            # Robust JSON extraction: handles terminal warnings preceding or trailing the JSON payload
            json_start = stdout.find("{")
            json_end = stdout.rfind("}")
            if json_start != -1 and json_end != -1:
                clean_json_str = stdout[json_start : json_end + 1]
                try:
                    parsed = json.loads(clean_json_str)
                    return parsed
                except json.JSONDecodeError as jde:
                    logger.error(f"Failed to parse Semgrep JSON output: {clean_json_str[:300]}")
                    raise RuntimeError(f"Semgrep returned invalid JSON: {clean_json_str[:150]}") from jde
            else:
                return {"results": [], "errors": []}

        except subprocess.TimeoutExpired as exc:
            logger.error(f"Semgrep scan timed out after {timeout_sec} seconds")
            raise TimeoutError(f"Semgrep scan timed out after {timeout_sec}s") from exc
        except Exception as e:
            logger.error(f"Unexpected error running Semgrep: {str(e)}")
            raise
