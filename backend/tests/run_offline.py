"""Run regression tests with external processes and remote connections forbidden."""
import os
from pathlib import Path
import sys
import unittest


def offline_guard(event, args):
    if event in {"subprocess.Popen", "os.system", "os.posix_spawn", "os.exec"}:
        raise AssertionError("Offline tests cannot start scanners, models or other external processes")
    if event == "socket.connect":
        address = args[1]
        if not isinstance(address, tuple) or address[0] not in {"127.0.0.1", "::1"}:
            raise AssertionError("Offline tests allow only localhost connections")


if __name__ == "__main__":
    directory = Path(os.environ.get("ARKTIC_TEST_DIR", Path(__file__).parent))
    sys.path.insert(0, str(directory))
    sys.addaudithook(offline_guard)
    suite = unittest.defaultTestLoader.discover(str(directory), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    raise SystemExit(not result.wasSuccessful())
