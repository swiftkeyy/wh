import pytest

from app.services.admin import AdminService


@pytest.mark.asyncio
async def test_admin_audit_report_includes_alerts(monkeypatch: pytest.MonkeyPatch) -> None:
    service = AdminService()

    async def fake_snapshot(limit: int = 5):
        return {"purchases": [], "ledger": [], "failed_jobs": []}

    async def fake_issues(limit: int = 5):
        return [{"type": "missing_ledger_grant", "purchase_id": "p-1", "status": "n/a"}]

    monkeypatch.setattr(service, "get_audit_snapshot", fake_snapshot)
    monkeypatch.setattr(service.alerting_service, "get_payment_integrity_issues", fake_issues)

    text = await service.get_audit_report_text()
    assert "Alerts" in text
    assert "missing_ledger_grant" in text
