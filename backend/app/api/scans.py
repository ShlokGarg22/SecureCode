import os
import shutil
import asyncio
from pathlib import Path
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

from app.core.config import settings
from app.core.extractor import ArchiveSecurityError
from app.models.scan import ScanResult, ScanStatus, ScanComparisonResult
from app.engine.orchestrator import orchestrator
from app.engine.comparator import compare_scans
from app.engine.patch_generator import generate_unified_patch
from app.engine.sarif_exporter import generate_sarif_report
from app.db.database import get_scan, list_scans

router = APIRouter(prefix="/api/scans", tags=["Scans"])


@router.post("/upload", response_model=ScanResult)
async def upload_and_scan(
    file: UploadFile = File(..., description="Project source code ZIP archive"),
    project_name: Optional[str] = Form(None, description="Optional custom project name"),
    rule_mode: str = Form("bundled", description="Rule set mode: bundled, online, or hybrid"),
    enable_ai: bool = Form(True, description="Enable AI or deterministic explanations"),
    custom_rules: Optional[str] = Form(None, description="Optional custom Semgrep rule pack")
):
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip archives are supported.")

    # Save uploaded file safely into uploads directory
    temp_zip_path = settings.data_dir / "uploads" / f"upload_{file.filename}"
    temp_zip_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Check size during streaming write
        total_bytes = 0
        with open(temp_zip_path, "wb") as buffer:
            while True:
                chunk = await file.read(64 * 1024)
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > settings.max_upload_size_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Uploaded ZIP exceeds maximum limit of {settings.max_upload_size_bytes} bytes."
                    )
                buffer.write(chunk)

        result = await asyncio.to_thread(
            orchestrator.scan_project_archive,
            zip_path=temp_zip_path,
            project_name=project_name or file.filename.replace(".zip", ""),
            rule_mode=rule_mode,
            enable_ai=enable_ai,
            custom_rules=custom_rules
        )
        return result

    except HTTPException:
        raise
    except ArchiveSecurityError as ase:
        raise HTTPException(status_code=400, detail=str(ase))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan execution error: {str(e)}")
    finally:
        # Clean up temporary uploaded zip
        if temp_zip_path.exists():
            try:
                temp_zip_path.unlink()
            except Exception:
                pass


@router.get("", response_model=List[ScanStatus])
def get_all_scans(limit: int = Query(50, ge=1, le=200)):
    """Retrieve historical scans summary."""
    return list_scans(limit=limit)


@router.get("/{scan_id}", response_model=ScanResult)
def get_scan_details(scan_id: str):
    """Retrieve full scan details and findings."""
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")
    return scan


@router.get("/{base_scan_id}/compare/{target_scan_id}", response_model=ScanComparisonResult)
def compare_scan_results(base_scan_id: str, target_scan_id: str):
    """Compare two scans of the same project to verify fixed vs new issues."""
    base_scan = get_scan(base_scan_id)
    if not base_scan:
        raise HTTPException(status_code=404, detail=f"Base scan '{base_scan_id}' not found.")

    target_scan = get_scan(target_scan_id)
    if not target_scan:
        raise HTTPException(status_code=404, detail=f"Target scan '{target_scan_id}' not found.")

    comparison = compare_scans(base_scan, target_scan)
    return comparison


@router.get("/{scan_id}/export/json")
def export_json_report(scan_id: str):
    """Download standardized JSON security report."""
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")
    return JSONResponse(
        content=scan.model_dump(mode="json"),
        headers={"Content-Disposition": f"attachment; filename=diffguard-{scan_id}.json"}
    )


@router.get("/{scan_id}/export/patch")
def export_patch_file(scan_id: str):
    """Download Git unified patch for one-command remediation via `git apply`."""
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")
    patch_content = generate_unified_patch(scan.findings, scan_id=scan.scan_id)
    return PlainTextResponse(
        content=patch_content,
        media_type="text/x-diff",
        headers={"Content-Disposition": f"attachment; filename=remediation-{scan_id}.patch"}
    )


@router.get("/{scan_id}/export/sarif")
def export_sarif_report(scan_id: str):
    """Download OASIS SARIF v2.1.0 report for GitHub Security / IDE ingestion."""
    scan = get_scan(scan_id)
    if not scan:
        raise HTTPException(status_code=404, detail=f"Scan '{scan_id}' not found.")
    sarif_data = generate_sarif_report(scan)
    return JSONResponse(
        content=sarif_data,
        headers={"Content-Disposition": f"attachment; filename=diffguard-{scan_id}.sarif"}
    )

