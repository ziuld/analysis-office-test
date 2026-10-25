"""Process boundaries; module entry points work independently of /app paths."""
import subprocess
import sys


def run_audit(job_id, repository):
    result = subprocess.run([sys.executable, "-m", "arktic_office.cli", repository, "--job-id", job_id],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1500, check=False)
    return result.returncode
