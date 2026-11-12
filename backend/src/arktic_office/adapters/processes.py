"""Process boundaries; module entry points work independently of /app paths."""
import subprocess
import sys
from arktic_office.config.models import integer


def run_audit(job_id, repository=None, *, local_snapshot=None, full_stack=False, private_ai_confirmed=False):
    source = ['--local-snapshot',str(local_snapshot)] if local_snapshot is not None else [repository]
    if full_stack:
        source.append("--full-stack")
    if private_ai_confirmed:
        source.append("--private-ai-confirmed")
    timeout = integer("AUDIT_JOB_TIMEOUT_SECONDS", 2700, 60, 86400)
    result = subprocess.run([sys.executable, "-m", "arktic_office.cli", *source, "--job-id", job_id],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout, check=False)
    return result.returncode
