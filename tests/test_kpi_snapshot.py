import pytest
from ghl_real_estate_ai.services.performance_monitoring_service import PerformanceMonitoringService


def test_kpi_snapshot_records_latest_values():
    monitor = PerformanceMonitoringService()
    monitor.record_kpi_event('leads_processed', 25, {'source': 'synthetic'})
    snapshot = monitor.get_kpi_snapshot()
    assert 'leads_processed' in snapshot
    assert snapshot['leads_processed']['value'] == 25
