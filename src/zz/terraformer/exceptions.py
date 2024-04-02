class TerraformError(Exception):
    pass


class TerraformRuntimeError(TerraformError):
    def __init__(self, message, process_results) -> None:
        self.process_results = process_results
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"{self.message} \n Return Code: {self.process_results.returncode} \n\n STDOUT: \n {self.process_results.stdout} \n\n STDERR: \n {self.process_results.stderr}"


class TerraformVersionError(TerraformError):
    pass
