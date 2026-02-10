import pytest

from runtime_metrics import RuntimeMetricsRegistry
import jorge_fastapi_lead_bot as lead_api


def test_growth_feature_flag_canary_mismatch_records_telemetry(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api.settings, "ff_growth_adaptive_followup_timing", True)
    monkeypatch.setattr(lead_api.settings, "ff_growth_canary_mode", True)
    monkeypatch.setattr(lead_api.settings, "ff_growth_canary_source", "facebook")

    enabled, reason = lead_api._evaluate_growth_feature(
        feature_name="adaptive_followup_timing",
        lead_source="google_ads",
    )

    assert enabled is False
    assert reason == "canary_source_mismatch"

    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert counters["feature_flag_evaluations_total"]["adaptive_followup_timing"] == 1
    assert counters["feature_flag_blocked_total"]["adaptive_followup_timing"] == 1
    assert counters["feature_flag_blocked_total"]["adaptive_followup_timing:canary_source_mismatch"] == 1


def test_adaptive_followup_passthrough_when_flag_disabled(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())

    follow_up_payload = {"type": "sms", "delay_minutes": 60}
    updated = lead_api._apply_adaptive_follow_up_timing(
        follow_up_data=follow_up_payload,
        analysis_result={"lead_score": 92, "jorge_priority": "high", "lead_temperature": "HOT"},
        lead_source="facebook",
        feature_enabled=False,
        feature_reason="flag_disabled",
    )

    assert updated == follow_up_payload
    assert updated is follow_up_payload

    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert counters["growth_feature_events_total"]["adaptive_followup_timing:bypassed_flag_disabled"] == 1


def test_adaptive_followup_adjusts_delay_when_enabled(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())

    follow_up_payload = {"type": "sms"}
    updated = lead_api._apply_adaptive_follow_up_timing(
        follow_up_data=follow_up_payload,
        analysis_result={"lead_score": 90, "jorge_priority": "high", "lead_temperature": "HOT"},
        lead_source="facebook",
        feature_enabled=True,
        feature_reason="enabled",
    )

    assert updated["adaptive_timing_applied"] is True
    assert updated["timing_bucket"] == "immediate"
    assert updated["recommended_delay_minutes"] == 5
    assert updated["engagement_score"] >= 85

    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert counters["growth_feature_events_total"]["adaptive_followup_timing:applied_immediate"] == 1


def test_lead_source_attribution_tracks_telemetry_when_disabled(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api.settings, "ff_growth_lead_source_writeback", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_conversion_feedback_writeback", False)

    analysis_result = {
        "lead_score": 90,
        "jorge_priority": "high",
        "lead_temperature": "HOT",
        "follow_up": {"type": "sms"},
    }

    growth_context = lead_api._apply_lead_source_attribution_feedback(
        analysis_result=analysis_result,
        lead_source="Facebook Ads",
        feature_enabled=False,
        feature_reason="flag_disabled",
    )

    assert growth_context == {}
    assert "lead_source_attribution" not in analysis_result
    assert "conversion_feedback" not in analysis_result
    assert "metadata" not in analysis_result["follow_up"]

    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert (
        counters["growth_feature_events_total"]
        ["lead_source_attribution:source_observed_facebook_ads"]
        == 1
    )
    assert (
        counters["growth_feature_events_total"]
        ["lead_source_attribution:feedback_signal_observed_high_intent"]
        == 1
    )
    assert counters["growth_feature_events_total"]["lead_source_attribution:bypassed_flag_disabled"] == 1


def test_lead_source_attribution_enriches_analysis_when_enabled(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api.settings, "ff_growth_lead_source_writeback", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_conversion_feedback_writeback", False)

    analysis_result = {
        "lead_score": 88,
        "jorge_priority": "high",
        "lead_temperature": "HOT",
        "follow_up": {"type": "sms", "delay_minutes": 60},
    }

    growth_context = lead_api._apply_lead_source_attribution_feedback(
        analysis_result=analysis_result,
        lead_source="facebook",
        feature_enabled=True,
        feature_reason="enabled",
    )

    assert growth_context["attribution"]["source"] == "facebook"
    assert growth_context["attribution"]["model"] == "last_touch"
    assert growth_context["conversion_feedback"]["status"] == "pending"
    assert growth_context["conversion_feedback"]["signal"] == "high_intent"
    assert analysis_result["follow_up"]["metadata"]["lead_source"] == "facebook"
    assert analysis_result["follow_up"]["metadata"]["conversion_feedback_signal"] == "high_intent"

    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert counters["growth_feature_events_total"]["lead_source_attribution:follow_up_enriched"] == 1
    assert counters["growth_feature_events_total"]["lead_source_attribution:telemetry_only_mode"] == 1
    assert counters["growth_feature_events_total"]["lead_source_attribution:applied"] == 1


@pytest.mark.asyncio
async def test_update_ghl_contact_growth_writebacks_respect_toggles(monkeypatch):
    class FakeGHL:
        def __init__(self):
            self.field_updates = []
            self.tag_updates = []

        async def update_contact_custom_fields(self, contact_id, updates):
            self.field_updates.append((contact_id, updates))
            return True

        async def add_contact_tags(self, contact_id, tags):
            self.tag_updates.append((contact_id, tags))
            return True

    fake_ghl = FakeGHL()
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api, "ghl_client", fake_ghl)
    monkeypatch.setattr(lead_api.settings, "ff_growth_lead_source_writeback", True)
    monkeypatch.setattr(lead_api.settings, "ff_growth_conversion_feedback_writeback", True)

    await lead_api.update_ghl_contact(
        contact_id="contact-growth-1",
        location_id="loc-growth-1",
        analysis_result={
            "lead_score": 91,
            "lead_temperature": "HOT",
            "jorge_priority": "high",
            "estimated_commission": 10000,
        },
        growth_context={
            "attribution": {"source": "facebook", "model": "last_touch"},
            "conversion_feedback": {"status": "pending", "signal": "high_intent"},
        },
    )

    assert len(fake_ghl.field_updates) == 1
    updates = fake_ghl.field_updates[0][1]
    assert updates["lead_source_attribution"] == "facebook"
    assert updates["conversion_feedback_state"] == "pending"
    assert updates["conversion_feedback_signal"] == "high_intent"
    assert len(fake_ghl.tag_updates) == 1
    assert "Conversion-Signal-High-Intent" in fake_ghl.tag_updates[0][1]

    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert counters["growth_feature_events_total"]["lead_source_attribution:writeback_attribution_enabled"] == 1
    assert counters["growth_feature_events_total"]["lead_source_attribution:writeback_feedback_enabled"] == 1


@pytest.mark.asyncio
async def test_contact_update_conversion_feedback_telemetry(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api.settings, "ff_growth_lead_source_attribution", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_conversion_feedback_writeback", False)

    webhook = lead_api.GHLWebhook(
        type="contact.updated",
        location_id="loc-1",
        contact_id="contact-1",
        contact={"status": "Appointment Booked", "source": "facebook"},
    )
    result = await lead_api.handle_contact_update(webhook, background_tasks=None)

    assert result["status"] == "acknowledged"
    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert counters["feature_flag_evaluations_total"]["lead_source_attribution"] == 1
    assert (
        counters["growth_feature_events_total"]
        ["lead_source_attribution:conversion_feedback_observed_converted"]
        == 1
    )
    assert (
        counters["growth_feature_events_total"]
        ["lead_source_attribution:conversion_feedback_bypassed_flag_disabled"]
        == 1
    )


def test_ab_response_style_disabled_does_not_mutate_analysis(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    analysis_result = {
        "lead_score": 83,
        "jorge_priority": "high",
        "lead_temperature": "HOT",
    }

    assignment = lead_api._apply_ab_response_style_testing(
        analysis_result=analysis_result,
        contact_id="contact-ab-1",
        lead_source="facebook",
        feature_enabled=False,
        feature_reason="flag_disabled",
    )

    assert assignment == {}
    assert "response_style_experiment" not in analysis_result
    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert counters["growth_feature_events_total"]["ab_response_style_testing:assignment_observed"] == 1
    assert counters["growth_feature_events_total"]["ab_response_style_testing:bypassed_flag_disabled"] == 1


def test_ab_response_style_enabled_uses_deterministic_assignment(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    first_analysis = {"lead_score": 88, "jorge_priority": "high", "lead_temperature": "HOT"}
    second_analysis = {"lead_score": 88, "jorge_priority": "high", "lead_temperature": "HOT"}

    first = lead_api._apply_ab_response_style_testing(
        analysis_result=first_analysis,
        contact_id="contact-ab-deterministic",
        lead_source="facebook",
        feature_enabled=True,
        feature_reason="enabled",
    )
    second = lead_api._apply_ab_response_style_testing(
        analysis_result=second_analysis,
        contact_id="contact-ab-deterministic",
        lead_source="facebook",
        feature_enabled=True,
        feature_reason="enabled",
    )

    assert first["variant"] in {"A", "B"}
    assert first["variant"] == second["variant"]
    assert first["bucket"] == second["bucket"]
    assert first_analysis["response_style_experiment"]["segment"] == "hot_priority"

    counters = lead_api.metrics_registry.snapshot()["counters"]["growth_feature_events_total"]
    variant_key = "ab_response_style_testing:variant_a" if first["variant"] == "A" else "ab_response_style_testing:variant_b"
    assert counters[variant_key] == 2
    assert counters["ab_response_style_testing:segment_hot_priority"] == 2
    assert counters["ab_response_style_testing:applied"] == 2


def test_ab_response_style_canary_mismatch_is_blocked_with_telemetry(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api.settings, "ff_growth_ab_response_style_testing", True)
    monkeypatch.setattr(lead_api.settings, "ff_growth_canary_mode", True)
    monkeypatch.setattr(lead_api.settings, "ff_growth_canary_source", "facebook")

    enabled, reason = lead_api._evaluate_growth_feature(
        feature_name="ab_response_style_testing",
        lead_source="google_ads",
    )
    assert enabled is False
    assert reason == "canary_source_mismatch"

    analysis_result = {"lead_score": 75, "jorge_priority": "normal", "lead_temperature": "WARM"}
    lead_api._apply_ab_response_style_testing(
        analysis_result=analysis_result,
        contact_id="contact-ab-2",
        lead_source="google_ads",
        feature_enabled=enabled,
        feature_reason=reason,
    )

    counters = lead_api.metrics_registry.snapshot()["counters"]
    assert counters["feature_flag_blocked_total"]["ab_response_style_testing:canary_source_mismatch"] == 1
    assert counters["growth_feature_events_total"]["ab_response_style_testing:bypassed_canary_source_mismatch"] == 1
    assert "response_style_experiment" not in analysis_result


@pytest.mark.asyncio
async def test_generate_response_message_defaults_without_ab_variant():
    analysis_result = {"jorge_priority": "high"}
    message = await lead_api.generate_response_message(analysis_result)
    assert "If it's easier, I can text over two quick options to compare first." not in message


def test_sla_handoff_thresholds_disabled_no_mutation(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    analysis_result = {"lead_score": 96, "jorge_priority": "high", "lead_temperature": "HOT"}

    recommendation = lead_api._evaluate_sla_handoff_thresholds(
        analysis_result=analysis_result,
        follow_up_data={"timing_bucket": "immediate"},
        lead_source="facebook",
        elapsed_processing_ms=5000,
        feature_enabled=False,
        feature_reason="flag_disabled",
    )

    assert recommendation == {}
    assert "sla_handoff" not in analysis_result
    counters = lead_api.metrics_registry.snapshot()["counters"]["growth_feature_events_total"]
    assert counters["sla_handoff_thresholds:observed"] == 1
    assert counters["sla_handoff_thresholds:bypassed_flag_disabled"] == 1


def test_sla_handoff_thresholds_recommends_handoff_for_high_risk(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    recommendation = lead_api._evaluate_sla_handoff_thresholds(
        analysis_result={"lead_score": 91, "jorge_priority": "high", "lead_temperature": "HOT"},
        follow_up_data={"timing_bucket": "immediate"},
        lead_source="facebook",
        elapsed_processing_ms=3000,
        feature_enabled=True,
        feature_reason="enabled",
    )

    assert recommendation["needs_handoff"] is True
    assert recommendation["risk_level"] == "high"
    assert recommendation["reason_code"] == "sla_high_risk_contact_now"
    counters = lead_api.metrics_registry.snapshot()["counters"]["growth_feature_events_total"]
    assert counters["sla_handoff_thresholds:risk_high"] == 1
    assert counters["sla_handoff_thresholds:handoff_recommended"] == 1


def test_sla_handoff_thresholds_marks_medium_risk_without_handoff(monkeypatch):
    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    recommendation = lead_api._evaluate_sla_handoff_thresholds(
        analysis_result={"lead_score": 72, "jorge_priority": "normal", "lead_temperature": "WARM"},
        follow_up_data={"timing_bucket": "standard"},
        lead_source="facebook",
        elapsed_processing_ms=65000,
        feature_enabled=True,
        feature_reason="enabled",
    )

    assert recommendation["needs_handoff"] is False
    assert recommendation["risk_level"] == "medium"
    counters = lead_api.metrics_registry.snapshot()["counters"]["growth_feature_events_total"]
    assert counters["sla_handoff_thresholds:risk_medium"] == 1
    assert counters["sla_handoff_thresholds:handoff_not_required"] == 1


@pytest.mark.asyncio
async def test_handle_lead_webhook_sla_disabled_preserves_default_payload(monkeypatch):
    class TaskCollector:
        def __init__(self):
            self.tasks = []

        def add_task(self, func, *args, **kwargs):
            self.tasks.append((func, args, kwargs))

    async def fake_analyze_lead_for_jorge(*args, **kwargs):
        return {
            "lead_score": 94,
            "lead_temperature": "HOT",
            "jorge_priority": "high",
            "estimated_commission": 15000,
            "actions": [],
            "follow_up": {"type": "sms", "delay_minutes": 60},
            "performance": {"cache_hit": False},
        }

    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api.settings, "ff_growth_lead_source_attribution", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_adaptive_followup_timing", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_ab_response_style_testing", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_sla_handoff_thresholds", False)
    monkeypatch.setattr(lead_api, "analyze_lead_for_jorge", fake_analyze_lead_for_jorge)

    tasks = TaskCollector()
    webhook = lead_api.GHLWebhook(
        type="message.received",
        location_id="loc-1",
        contact_id="contact-sla-1",
        contact={"source": "facebook"},
        message="Need to move fast",
    )
    result = await lead_api.handle_lead_webhook(webhook, tasks)

    assert result["status"] == "processed"
    update_call = next(call for call in tasks.tasks if call[0].__name__ == "update_ghl_contact")
    scheduled_analysis = update_call[1][2]
    assert "sla_handoff" not in scheduled_analysis

    follow_up_call = next(call for call in tasks.tasks if call[0].__name__ == "schedule_follow_up")
    scheduled_follow_up = follow_up_call[1][1]
    assert "metadata" not in scheduled_follow_up
    counters = lead_api.metrics_registry.snapshot()["counters"]["growth_feature_events_total"]
    assert counters["sla_handoff_thresholds:bypassed_flag_disabled"] == 1


@pytest.mark.asyncio
async def test_handle_lead_webhook_preserves_legacy_non_dict_follow_up_payload(monkeypatch):
    class TaskCollector:
        def __init__(self):
            self.tasks = []

        def add_task(self, func, *args, **kwargs):
            self.tasks.append((func, args, kwargs))

    async def fake_analyze_lead_for_jorge(*args, **kwargs):
        return {
            "lead_score": 72,
            "lead_temperature": "WARM",
            "jorge_priority": "normal",
            "estimated_commission": 7500,
            "actions": [],
            "follow_up": "legacy-follow-up-token",
            "performance": {"cache_hit": False},
        }

    monkeypatch.setattr(lead_api, "metrics_registry", RuntimeMetricsRegistry())
    monkeypatch.setattr(lead_api.settings, "ff_growth_lead_source_attribution", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_adaptive_followup_timing", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_ab_response_style_testing", False)
    monkeypatch.setattr(lead_api.settings, "ff_growth_sla_handoff_thresholds", False)
    monkeypatch.setattr(lead_api, "analyze_lead_for_jorge", fake_analyze_lead_for_jorge)

    tasks = TaskCollector()
    webhook = lead_api.GHLWebhook(
        type="message.received",
        location_id="loc-legacy-follow-up",
        contact_id="contact-legacy-follow-up",
        contact={"source": "facebook"},
        message="Following up on listing details",
    )
    result = await lead_api.handle_lead_webhook(webhook, tasks)

    assert result["status"] == "processed"
    follow_up_call = next(call for call in tasks.tasks if call[0].__name__ == "schedule_follow_up")
    assert follow_up_call[1][1] == "legacy-follow-up-token"
