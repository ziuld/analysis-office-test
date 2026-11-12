"""Iris entry points retained for callers and archived evaluation launchers."""
from arktic_office.coordination.workflow import (
    SYNTHESIS,
    checkpoint_path,
    interrupt,
    load_tasks,
    research as run_workflow,
)


def research(snapshot, config, state, evidence, budget, output, cells):
    return run_workflow(snapshot, config, state, evidence, budget, output, cells, tasks=load_tasks())
