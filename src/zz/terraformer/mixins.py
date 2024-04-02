import os
import subprocess
from logging import getLogger
from typing import IO, Any, Dict, cast

from .exceptions import TerraformRuntimeError

logger = getLogger(__name__)

DEFAULT_ENV_VARS = {"TF_IN_AUTOMATION": "1", "TF_INPUT": "0"}


class ProcessResults:
    def __init__(self, returncode, stdout, stderr) -> None:
        self.returncode = returncode
        self.successful = returncode == 0
        self.stdout = stdout
        self.stderr = stderr
        self.env: Dict[str, Any] = {}


class TerraformRun:
    cwd: str = os.getcwd()
    env: Dict[str, str] = {}

    def _subprocess_run(self, args, raise_exception_on_failure=False, **kwargs) -> ProcessResults:
        default_kwargs = {
            "cwd": self.cwd,
            "capture_output": True,
            "encoding": "utf-8",
            "timeout": None,
            "env": {**os.environ, **DEFAULT_ENV_VARS, **self.env},
        }
        pass_kwargs = {**default_kwargs, **kwargs}
        results = subprocess.run(args, **pass_kwargs)  # type: ignore

        ret_results = ProcessResults(results.returncode, results.stdout, results.stderr)

        if raise_exception_on_failure and not ret_results.successful:
            error_message = f"An error occurred while running command '{' '.join(args)}'\n"
            error_message += f"returncode: {ret_results.returncode}\n"
            error_message += f"stdout: {ret_results.stdout}\n"
            error_message += f"stderr: {ret_results.stderr}\n"
            raise TerraformRuntimeError(error_message, ret_results)

        return ret_results

    def _subprocess_stream(self, command, error_function=None, output_function=None, **kwargs) -> ProcessResults:
        logger.info(f"Running command '{command}'")
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self.cwd,
            env={**os.environ, **DEFAULT_ENV_VARS, **self.env},
            universal_newlines=True,
            encoding="utf-8",
            bufsize=1,
            **kwargs,
        )
        stdout = ""
        stderr = ""
        while True:
            had_output = False

            # Check for stdout changes.
            for output in cast(IO, process.stdout):
                stdout += output
                logger.info(output)
                if output_function:
                    output_function(output)

            # Check for stderr changes.
            for output in cast(IO, process.stderr):
                had_output = True
                stderr += output
                logger.warning(output)
                if error_function:
                    error_function(output)

            # Process is closed and we've read all of the outputs.
            if process.poll() is not None:
                if not had_output:
                    break

        # Match the return object of subprocess.run.
        return ProcessResults(returncode=process.poll(), stdout=stdout, stderr=stderr)
