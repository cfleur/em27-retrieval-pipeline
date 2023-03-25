import os
import sys
import click
import tum_esm_utils
from utils import print_green, print_red

PROJECT_DIR = tum_esm_utils.files.get_parent_dir_path(__file__, current_depth=3)
RUN_SCRIPT_PATH = os.path.join(PROJECT_DIR, "src", "run_automated_proffast.py")


@click.command(
    help="Start the automated proffast as a background "
    + "process. Prevents spawning multiple processes"
)
def _start() -> None:
    new_pid = tum_esm_utils.processes.start_background_process(
        sys.executable, RUN_SCRIPT_PATH
    )
    print_green(f"Started automated proffast background process with PID {new_pid}")


@click.command(
    help="Checks whether the automated proffast background process is running"
)
def _is_running() -> None:
    existing_pids = tum_esm_utils.processes.get_process_pids(RUN_SCRIPT_PATH)
    if len(existing_pids) > 0:
        print_green(f"automated proffast is running with PID(s) {existing_pids}")
    else:
        print_red("automated proffast is not running")


@click.command(help="Stop the automated proffast background process")
def _stop() -> None:
    termination_pids = tum_esm_utils.processes.terminate_process(RUN_SCRIPT_PATH)
    if len(termination_pids) == 0:
        print_red("No active process to be terminated")
    else:
        print_green(
            f"Terminated {len(termination_pids)} automated proffast "
            + f"background processe(s) with PID(s) {termination_pids}"
        )


@click.group()
def automated_proffast_command_group() -> None:
    pass


automated_proffast_command_group.add_command(_start, name="start")
automated_proffast_command_group.add_command(_stop, name="stop")
automated_proffast_command_group.add_command(_is_running, name="is-running")
