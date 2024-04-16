from pydantic import BaseSettings


class Settings(BaseSettings):
    project_name: str = "terraformer"
    debug: bool = False
    plan_sensitive_data_replace_with: str = "(sensitive)"
    plan_known_after_apply_replace_with: str = "(known after apply)"
