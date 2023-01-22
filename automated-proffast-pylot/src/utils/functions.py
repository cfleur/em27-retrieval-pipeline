from datetime import datetime
import os
import random
import subprocess
from typing import Optional
import string

dirname = os.path.dirname
PROJECT_DIR = dirname(dirname(dirname(os.path.abspath(__file__))))


def get_commit_sha() -> Optional[str]:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "--verify", "HEAD"],
                cwd=PROJECT_DIR,
            )
            .decode()
            .replace("\n", "")
        )
    except:
        return None


def load_file(path: str) -> str:
    with open(path, "r") as f:
        return "".join(f.readlines())


def dump_file(path: str, content: str) -> None:
    with open(path, "w") as f:
        f.write(content)


def insert_replacements(content: str, replacements: dict[str, str]) -> str:
    for key, value in replacements.items():
        content = content.replace(f"%{key}%", value)
    return content


def is_date_string(date_string: str) -> bool:
    try:
        datetime.strptime(date_string, "%Y%m%d")
        return True
    except (AssertionError, ValueError):
        return False


def date_is_too_recent(
    date_string: str,
    min_days_delay: int = 1,
) -> bool:
    date_object = datetime.strptime(
        date_string, "%Y%m%d"
    )  # will have the time 00:00:00
    return (datetime.now() - date_object).days >= min_days_delay


def get_random_string(length: int, forbidden: list[str] = []) -> str:
    """a random string from lowercase letter, the strings from
    the list passed as `forbidden` will not be generated"""
    output: str = ""
    while True:
        output = "".join(random.choices(string.ascii_lowercase, length))
        if output not in forbidden:
            break
    return output


import subprocess
from typing import Optional


def run_shell_command(command: str, working_directory: Optional[str] = None) -> str:
    p = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_directory,
    )
    stdout = p.stdout.decode("utf-8", errors="replace")
    stderr = p.stderr.decode("utf-8", errors="replace")

    assert p.returncode == 0, (
        f"command '{command}' failed with exit code "
        + f"{p.returncode}: stderr = '{stderr}'"
    )
    return stdout.strip()
