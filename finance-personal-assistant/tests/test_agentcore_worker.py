import asyncio
import unittest
from unittest.mock import patch

import worker as agentcore_worker


class WorkerLifecycleTests(unittest.IsolatedAsyncioTestCase):
    async def asyncTearDown(self):
        task = agentcore_worker._worker
        if task is not None and not task.done():
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        agentcore_worker._worker = None

    async def test_duplicate_invocation_starts_one_worker_and_releases_task(self):
        started = asyncio.Event()
        release = asyncio.Event()

        async def run_worker():
            started.set()
            await release.wait()

        with (
            patch.object(agentcore_worker, "run_temporal_worker", side_effect=run_worker) as run,
            patch.object(agentcore_worker.app, "add_async_task", return_value=42) as add,
            patch.object(agentcore_worker.app, "complete_async_task") as complete,
        ):
            first = await agentcore_worker.invoke({})
            await started.wait()
            second = await agentcore_worker.invoke({})
            self.assertEqual(first["message"], "worker starting")
            self.assertEqual(second["message"], "worker already polling")
            self.assertEqual(run.call_count, 1)
            add.assert_called_once()
            release.set()
            await agentcore_worker._worker
            complete.assert_called_once_with(42)

    async def test_failure_releases_agentcore_async_task(self):
        async def fail():
            raise RuntimeError("Temporal is unavailable")

        with (
            patch.object(agentcore_worker, "run_temporal_worker", side_effect=fail),
            patch.object(agentcore_worker.app, "add_async_task", return_value=7),
            patch.object(agentcore_worker.app, "complete_async_task") as complete,
            patch.object(agentcore_worker.log, "exception") as logged,
        ):
            await agentcore_worker.invoke({})
            await agentcore_worker._worker
            complete.assert_called_once_with(7)
            logged.assert_called_once()

    async def test_idle_wait_does_not_drain_running_activity(self):
        tracker = agentcore_worker.ActivityTracker()
        started = asyncio.Event()
        release = asyncio.Event()

        class Next:
            async def execute_activity(self, input):
                started.set()
                await release.wait()

        tracked = agentcore_worker._TrackedActivity(Next(), tracker)
        activity_task = asyncio.create_task(tracked.execute_activity(None))
        await started.wait()
        idle_task = asyncio.create_task(tracker.wait_until_idle(0.02))
        await asyncio.sleep(0.06)
        self.assertFalse(idle_task.done())
        release.set()
        await activity_task
        await asyncio.wait_for(idle_task, timeout=1)
        self.assertEqual(tracker.inflight, 0)


if __name__ == "__main__":
    unittest.main()
