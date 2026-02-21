"""Tests for JobScheduler: cron expressions, job management, triggers."""

from datetime import datetime

import pytest

from devops_suite.data_pipeline.scheduler import JobScheduler


@pytest.fixture
def scheduler():
    return JobScheduler()


class TestJobScheduler:
    def test_add_job(self, scheduler):
        job = scheduler.add_job(
            job_id="job-1",
            name="Daily Job",
            cron_expression="0 0 * * *",
        )
        assert job.job_id == "job-1"
        assert job.name == "Daily Job"
        assert job.is_active is True

    def test_add_job_with_callback(self, scheduler):
        executed = []

        def callback():
            executed.append(True)

        job = scheduler.add_job(
            job_id="job-1",
            name="Test",
            cron_expression="* * * * *",
            callback=callback,
        )
        assert job.callback is not None

    def test_add_job_invalid_cron(self, scheduler):
        with pytest.raises(ValueError, match="Invalid cron expression"):
            scheduler.add_job("job-1", "Test", "invalid cron")

    def test_add_job_with_metadata(self, scheduler):
        job = scheduler.add_job(
            "job-1",
            "Test",
            "0 * * * *",
            metadata={"owner": "admin", "priority": "high"},
        )
        assert job.metadata["owner"] == "admin"
        assert job.metadata["priority"] == "high"

    def test_remove_job(self, scheduler):
        scheduler.add_job("job-1", "Test", "0 * * * *")
        removed = scheduler.remove_job("job-1")
        assert removed is True
        assert scheduler.get_job("job-1") is None

    def test_remove_nonexistent_job(self, scheduler):
        removed = scheduler.remove_job("fake-job")
        assert removed is False

    def test_get_job(self, scheduler):
        scheduler.add_job("job-1", "Test", "0 * * * *")
        job = scheduler.get_job("job-1")
        assert job is not None
        assert job.job_id == "job-1"

    def test_get_nonexistent_job(self, scheduler):
        job = scheduler.get_job("fake-job")
        assert job is None

    def test_list_jobs(self, scheduler):
        scheduler.add_job("job-1", "Job 1", "0 * * * *")
        scheduler.add_job("job-2", "Job 2", "0 0 * * *")
        scheduler.add_job("job-3", "Job 3", "0 0 1 * *")
        jobs = scheduler.list_jobs()
        assert len(jobs) == 3
        assert {j.job_id for j in jobs} == {"job-1", "job-2", "job-3"}

    def test_pause_job(self, scheduler):
        scheduler.add_job("job-1", "Test", "0 * * * *")
        paused = scheduler.pause_job("job-1")
        assert paused is True
        job = scheduler.get_job("job-1")
        assert job.is_active is False

    def test_pause_nonexistent_job(self, scheduler):
        paused = scheduler.pause_job("fake-job")
        assert paused is False

    def test_resume_job(self, scheduler):
        scheduler.add_job("job-1", "Test", "0 * * * *")
        scheduler.pause_job("job-1")
        resumed = scheduler.resume_job("job-1")
        assert resumed is True
        job = scheduler.get_job("job-1")
        assert job.is_active is True

    def test_resume_nonexistent_job(self, scheduler):
        resumed = scheduler.resume_job("fake-job")
        assert resumed is False

    def test_list_active_jobs(self, scheduler):
        scheduler.add_job("job-1", "Active", "0 * * * *")
        scheduler.add_job("job-2", "Paused", "0 0 * * *")
        scheduler.pause_job("job-2")
        active = scheduler.list_active_jobs()
        assert len(active) == 1
        assert active[0].job_id == "job-1"

    def test_trigger_job(self, scheduler):
        executed = []

        def callback():
            executed.append(True)

        scheduler.add_job("job-1", "Test", "0 * * * *", callback=callback)
        triggered = scheduler.trigger_job("job-1")
        assert triggered is True
        assert len(executed) == 1

    def test_trigger_job_updates_run_count(self, scheduler):
        def noop():
            pass

        scheduler.add_job("job-1", "Test", "0 * * * *", callback=noop)
        scheduler.trigger_job("job-1")
        scheduler.trigger_job("job-1")
        job = scheduler.get_job("job-1")
        assert job.run_count == 2

    def test_trigger_job_updates_last_run(self, scheduler):
        def noop():
            pass

        scheduler.add_job("job-1", "Test", "0 * * * *", callback=noop)
        before = datetime.utcnow()
        scheduler.trigger_job("job-1")
        job = scheduler.get_job("job-1")
        assert job.last_run is not None
        assert job.last_run >= before

    def test_trigger_job_without_callback(self, scheduler):
        scheduler.add_job("job-1", "Test", "0 * * * *")
        triggered = scheduler.trigger_job("job-1")
        assert triggered is False

    def test_trigger_nonexistent_job(self, scheduler):
        triggered = scheduler.trigger_job("fake-job")
        assert triggered is False

    def test_update_cron(self, scheduler):
        scheduler.add_job("job-1", "Test", "0 * * * *")
        updated = scheduler.update_cron("job-1", "0 0 * * *")
        assert updated is True
        job = scheduler.get_job("job-1")
        assert job.cron_expression == "0 0 * * *"

    def test_update_cron_invalid(self, scheduler):
        scheduler.add_job("job-1", "Test", "0 * * * *")
        with pytest.raises(ValueError, match="Invalid cron expression"):
            scheduler.update_cron("job-1", "bad cron")

    def test_update_cron_nonexistent_job(self, scheduler):
        updated = scheduler.update_cron("fake-job", "0 * * * *")
        assert updated is False

    def test_cron_validation_five_fields(self, scheduler):
        job = scheduler.add_job("job-1", "Test", "0 1 2 3 4")
        assert job is not None

    def test_cron_validation_six_fields(self, scheduler):
        job = scheduler.add_job("job-1", "Test", "0 1 2 3 4 5")
        assert job is not None

    def test_cron_validation_wildcard(self, scheduler):
        job = scheduler.add_job("job-1", "Test", "* * * * *")
        assert job is not None

    def test_multiple_jobs_independent(self, scheduler):
        exec_log = []

        def callback1():
            exec_log.append("job1")

        def callback2():
            exec_log.append("job2")

        scheduler.add_job("job-1", "J1", "* * * * *", callback=callback1)
        scheduler.add_job("job-2", "J2", "0 * * * *", callback=callback2)

        scheduler.trigger_job("job-1")
        scheduler.trigger_job("job-2")
        scheduler.trigger_job("job-1")

        assert exec_log == ["job1", "job2", "job1"]

    def test_job_isolation(self, scheduler):
        scheduler.add_job("job-1", "J1", "* * * * *", metadata={"key": "value1"})
        scheduler.add_job("job-2", "J2", "0 * * * *", metadata={"key": "value2"})

        job1 = scheduler.get_job("job-1")
        job2 = scheduler.get_job("job-2")

        assert job1.metadata["key"] == "value1"
        assert job2.metadata["key"] == "value2"
