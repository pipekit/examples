"""Run the demand forecast job from the terminal.

The same job the notebook runs, as a plain script. Submits to Pipekit, prints a link
to watch it live, waits for completion, and exits non-zero if the run fails.
"""

import sys

from dataplatform import logs, run, wait
from forecast_step import forecast_demand

result = run("daily-demand-forecast", forecast_demand)
status = wait(result)
print(f"run status: {status}")

logs(result)

sys.exit(0 if status == "completed" else 1)
