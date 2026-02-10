"""
Evidence Pack Export
Creates a ZIP bundle with validation reports and KPI snapshot.
"""

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pathlib import Path
from datetime import datetime
from io import BytesIO
import json
import zipfile

from ghl_real_estate_ai.services.performance_monitoring_service import performance_monitor

router = APIRouter(prefix="/api", tags=["evidence_pack"])


@router.get("/evidence-pack")
async def export_evidence_pack():
    base_dir = Path(__file__).resolve().parents[3]
    files = [
        base_dir / "performance_validation_report.md",
        base_dir / "security_validation_report_20260120_050503.md",
        base_dir / "DEPLOYMENT_CHECKLIST.md",
    ]

    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files:
            if file_path.exists():
                zipf.write(file_path, arcname=file_path.name)

        # KPI snapshot
        snapshot = performance_monitor.get_kpi_snapshot()
        manifest = {
            "generated_at": datetime.utcnow().isoformat(),
            "kpi_snapshot": snapshot,
            "notes": "Evidence pack includes validation reports and KPI telemetry snapshot"
        }
        zipf.writestr("kpi_snapshot.json", json.dumps(snapshot, indent=2))
        zipf.writestr("manifest.json", json.dumps(manifest, indent=2))

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=enterprisehub-evidence-pack.zip"
        }
    )
