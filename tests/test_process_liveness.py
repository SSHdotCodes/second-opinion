import contextlib
import ctypes
from ctypes import wintypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

from test_cli import CLI, load_cli_module


class ProcessLivenessTests(unittest.TestCase):
    @contextlib.contextmanager
    def windows_probe(self, *, handle=0x123456789, wait_result=258, error=0):
        module = load_cli_module()
        fake_os = mock.Mock(wraps=os)
        fake_os.name = "nt"
        fake_os.kill.side_effect = AssertionError("Status checks must not signal workers")
        kernel32 = mock.Mock()
        kernel32.OpenProcess.return_value = handle
        kernel32.WaitForSingleObject.return_value = wait_result
        with (
            mock.patch.object(module, "os", fake_os),
            mock.patch.object(ctypes, "WinDLL", return_value=kernel32, create=True) as loader,
            mock.patch.object(ctypes, "get_last_error", return_value=error, create=True),
            mock.patch.object(ctypes, "WinError", return_value=OSError(error, "Win32 error"), create=True),
        ):
            yield module, kernel32, loader
        fake_os.kill.assert_not_called()

    def test_windows_live_and_exited_processes_use_read_only_handles(self):
        for wait_result, expected in ((258, True), (0, False)):
            with self.subTest(wait_result=wait_result), self.windows_probe(wait_result=wait_result) as probe:
                module, kernel32, loader = probe
                self.assertEqual(module.is_process_running(1234), expected)
                loader.assert_called_once_with("kernel32", use_last_error=True)
                kernel32.OpenProcess.assert_called_once_with(0x00100000, False, 1234)
                kernel32.WaitForSingleObject.assert_called_once_with(0x123456789, 0)
                kernel32.CloseHandle.assert_called_once_with(0x123456789)
                # HANDLE must be pointer-sized on 64-bit Windows.
                self.assertIs(kernel32.OpenProcess.restype, wintypes.HANDLE)
                self.assertEqual(kernel32.WaitForSingleObject.argtypes, [wintypes.HANDLE, wintypes.DWORD])
                self.assertEqual(kernel32.CloseHandle.argtypes, [wintypes.HANDLE])

    def test_windows_missing_and_access_denied_pids_do_not_crash(self):
        for error, expected in ((87, False), (5, True)):
            with self.subTest(error=error), self.windows_probe(handle=None, error=error) as probe:
                module, kernel32, _ = probe
                self.assertEqual(module.is_process_running(1234), expected)
                kernel32.WaitForSingleObject.assert_not_called()
                kernel32.CloseHandle.assert_not_called()

    def test_windows_unexpected_open_error_is_preserved(self):
        with self.windows_probe(handle=None, error=8) as (module, kernel32, _):
            with self.assertRaises(OSError) as raised:
                module.is_process_running(1234)
            self.assertEqual(raised.exception.errno, 8)
            kernel32.CloseHandle.assert_not_called()

    def test_windows_wait_failure_still_closes_handle(self):
        with self.windows_probe(wait_result=0xFFFFFFFF, error=6) as (module, kernel32, _):
            with self.assertRaises(OSError) as raised:
                module.is_process_running(1234)
            self.assertEqual(raised.exception.errno, 6)
            kernel32.CloseHandle.assert_called_once_with(0x123456789)

    def test_invalid_windows_pids_never_reach_the_os(self):
        with self.windows_probe() as (module, kernel32, loader):
            for pid in (0, -1, -1234, 0x100000000, 0x100000000 + os.getpid()):
                with self.subTest(pid=pid):
                    self.assertFalse(module.is_process_running(pid))
            loader.assert_not_called()
            kernel32.OpenProcess.assert_not_called()

    def test_posix_probe_keeps_existing_permission_and_lookup_behavior(self):
        module = load_cli_module()
        fake_os = mock.Mock(wraps=os)
        fake_os.name = "posix"
        with mock.patch.object(module, "os", fake_os):
            for error, expected in ((None, True), (ProcessLookupError(), False), (PermissionError(), True)):
                with self.subTest(error=error):
                    fake_os.kill.reset_mock()
                    fake_os.kill.side_effect = error
                    self.assertEqual(module.is_process_running(1234), expected)
                    fake_os.kill.assert_called_once_with(1234, 0)
            fake_os.kill.reset_mock()
            for pid in (0, -1):
                self.assertFalse(module.is_process_running(pid))
            fake_os.kill.assert_not_called()

    def test_job_status_uses_worker_pid_and_preserves_terminal_and_queued_states(self):
        with self.windows_probe() as (module, _, _):
            self.assertEqual(module.job_status({"worker_pid": 1234, "pid": 0, "state": "running"}), "running")
            self.assertEqual(module.job_status({"pid": 1234}), "running")
        with self.windows_probe(handle=None, error=87) as (module, _, _):
            for state in ("finished", "failed", "stopped"):
                self.assertEqual(module.job_status({"worker_pid": 1234, "state": state}), state)
            self.assertEqual(
                module.job_status({"worker_pid": 1234, "state": "running", "turns": [{"status": "queued"}]}),
                "queued",
            )

    @unittest.skipUnless(os.name == "nt", "Exercises real Windows process handles")
    def test_real_windows_process_exiting_with_259_is_not_reported_alive(self):
        module = load_cli_module()
        # GetExitCodeProcess alone would confuse exit code 259 with STILL_ACTIVE.
        with subprocess.Popen([sys.executable, "-c", "import sys; sys.exit(259)"]) as process:
            self.assertEqual(process.wait(timeout=10), 259)
            self.assertFalse(module.is_process_running(process.pid))
        self.assertFalse(module.is_process_running(0xFFFFFFFF))

    def test_jobs_and_wait_inspect_a_real_detached_worker_without_stopping_it(self):
        module = load_cli_module()
        with tempfile.TemporaryDirectory() as temp, mock.patch.dict(os.environ, {"SECOND_OPINION_HOME": temp}):
            root = Path(temp)
            ready = root / "ready"
            release = root / "release"
            # A bounded, credential-free harness keeps the actual worker alive.
            harness = (
                "from pathlib import Path\nimport sys, time\n"
                "ready, release = map(Path, sys.argv[1:])\n"
                "ready.touch()\ndeadline = time.monotonic() + 20\n"
                "while not release.exists() and time.monotonic() < deadline:\n"
                "    time.sleep(0.05)\n"
                "print('BACKGROUND_OK')\n"
            )
            job_id, pid = module.create_background_job(
                module.AGENTS["codex"], "consult",
                [sys.executable, "-c", harness, str(ready), str(release)],
                root, "Test live worker status",
            )
            worker = next(process for process in module.DETACHED_PROCESSES if process.pid == pid)
            waiter = None
            try:
                deadline = time.monotonic() + 10
                while not ready.exists() and worker.poll() is None and time.monotonic() < deadline:
                    time.sleep(0.05)
                self.assertTrue(ready.exists(), "Worker did not start its harness")
                for args in (("jobs",), ("jobs", "--json"), ("jobs", "--running", "--json")):
                    result = subprocess.run(
                        [sys.executable, str(CLI), *args], text=True,
                        capture_output=True, timeout=10, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    if "--json" in args:
                        jobs = json.loads(result.stdout)["jobs"]
                        self.assertEqual(len(jobs), 1)
                        self.assertEqual(jobs[0]["status"], "running")
                        self.assertEqual(jobs[0]["worker_pid"], pid)
                    else:
                        self.assertIn(job_id, result.stdout)
                        self.assertIn("running", result.stdout)
                    self.assertIsNone(worker.poll(), "Status query stopped the worker")
                waiter = subprocess.Popen(
                    [sys.executable, str(CLI), "wait", job_id, "--interval", "0.05"],
                    text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                # Give wait a chance to probe the still-running worker.
                time.sleep(0.25)
                self.assertIsNone(waiter.poll())
                self.assertIsNone(worker.poll())
                release.touch()
                stdout, stderr = waiter.communicate(timeout=10)
                self.assertEqual(waiter.returncode, 0, stderr)
                self.assertIn("BACKGROUND_OK", stdout)
                self.assertEqual(worker.wait(timeout=10), 0)
                job = module.read_job(job_id)
                self.assertEqual(module.job_status(job), "finished")
                self.assertIsNone(job["worker_pid"])
                self.assertFalse(module.is_process_running(pid))
            finally:
                release.touch()
                if waiter is not None:
                    if waiter.poll() is None:
                        waiter.kill()
                    waiter.communicate(timeout=10)
                try:
                    worker.wait(timeout=25)
                except subprocess.TimeoutExpired:
                    worker.kill()
                    worker.wait(timeout=10)
                module.reap_detached_processes()
