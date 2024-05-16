import json
import shutil
from copy import deepcopy
from logging import getLogger
from typing import Any
from typing import Dict

from .exceptions import TerraformRuntimeError
from .exceptions import TerraformVersionError
from .mixins import TerraformRun
from .settings import settings


logger = getLogger(__name__)

MODIFICATION_ACTIONS = ["update"]
DELETION_ACTIONS = ["delete"]
CREATE_ACTIONS = ["create"]

SANITIZE_REPLACE_WITH = settings.plan_sensitive_data_replace_with
KNOWN_AFTER_APPLY_REPLACE_WITH = settings.plan_known_after_apply_replace_with


class TerraformPlan(TerraformRun):
    changes: Dict[str, Any]
    env: Dict[str, str]

    def __init__(self, cwd, plan_path, is_json=False) -> None:
        # confirm file exists

        self.cwd = cwd
        self.env = {}
        self.plan_path = plan_path

        if not is_json:
            terraform_path = shutil.which("terraform")
            command = [terraform_path, "show", "-json", plan_path]
            results = self._subprocess_run(command)

            if results.returncode != 0:
                raise TerraformRuntimeError("Terraform plan failed", results)

            plan_details = json.loads(results.stdout)
        else:
            with open(plan_path) as plan_json:
                plan_details = json.load(plan_json)

        self.raw_plan = plan_details
        self.terraform_version = plan_details["terraform_version"]
        self.format_version = plan_details["format_version"]

        if self.format_version[:1] != "1":
            raise TerraformVersionError(
                f"Expected semantic version equivalent of v1, instead found '{self.format_version}'"
            )

        self.deletions = 0
        self.creations = 0
        self.modifications = 0

        self.changes = {}
        self._parse_changes(plan_details.get("resource_changes", []))

    def _parse_changes(self, change_plan: list):
        for changeset in change_plan:
            change = TerraformChange(changeset)
            self.changes[changeset["address"]] = TerraformChange(changeset)
            if change.will_delete():
                self.deletions += 1
            if change.will_create():
                self.creations += 1
            if change.will_modify():
                self.modifications += 1


class TerraformChange:
    def __init__(self, changeset) -> None:
        self.address = changeset["address"]
        self.type = changeset["type"]
        self.actions = changeset["change"]["actions"]

        # Capture the before, after changes and expose sanitized fields where the data is sensitive or unknown during plan.

        self.before = changeset["change"]["before"]
        self.before_sensitive = changeset["change"]["before_sensitive"]
        self.after = changeset["change"]["after"]
        self.after_sensitive = changeset["change"]["after_sensitive"]
        self.after_unknown = changeset["change"]["after_unknown"]

        self._sanitize_sensitive(SANITIZE_REPLACE_WITH)
        self._sanitize_unknown(KNOWN_AFTER_APPLY_REPLACE_WITH)

    def will_delete(self):
        return len(list(set(self.actions) & set(DELETION_ACTIONS))) > 0

    def will_modify(self):
        return len(list(set(self.actions) & set(MODIFICATION_ACTIONS))) > 0

    def will_create(self):
        return len(list(set(self.actions) & set(CREATE_ACTIONS))) > 0

    # Sanitize the sensitive data and create a `sanitized` copy so that it can be used with reporting tools directly.
    def _sanitize_sensitive(self, replace_with=SANITIZE_REPLACE_WITH):
        self.before_sanitized = TerraformChange._sanitize_change_value(
            deepcopy(self.before),
            self.before_sensitive,
            replace_with,  # send a copy so that the field itself isn't directly modified.
        )
        self.after_sanitized = TerraformChange._sanitize_change_value(
            deepcopy(self.after), self.after_sensitive, replace_with
        )

    # Sanitize the data that can be known only after apply and add to the `sanitized` copy so that it can be used with reporting tools directly.
    def _sanitize_unknown(self, replace_with=KNOWN_AFTER_APPLY_REPLACE_WITH):
        self.after_sanitized = TerraformChange._sanitize_change_value(
            deepcopy(self.after_sanitized), self.after_unknown, replace_with
        )

    def _sanitize_change_value(old_value, sanitizable, replace_with):
        if type(old_value) == type([]) and type(sanitizable) == type([]):
            for idx, sanitized in enumerate(sanitizable):
                if sanitized == True:
                    old_value[idx] = TerraformChange._sanitize_change_value(
                        old_value[idx], sanitizable[idx], replace_with
                    )

        elif type(old_value) == type({}) and type(sanitizable) == type({}):
            for key, value in sanitizable.items():
                if value:
                    old_value[key] = TerraformChange._sanitize_change_value(
                        old_value.get(key), sanitizable.get(key), replace_with
                    )

        if sanitizable == True:
            return replace_with

        return old_value
