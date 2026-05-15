from dotacoach.scheduler import build_scheduler


def test_build_scheduler_registers_weekly():
    fired = []

    def cb():
        fired.append(1)

    sched = build_scheduler(cb)
    jobs = sched.get_jobs()
    assert any(j.id == "weekly_review" for j in jobs)
