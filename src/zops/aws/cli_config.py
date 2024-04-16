import os
from pathlib import Path
import shutil

import yaml

from zops.aws.autoscaling import AutoScalingGroup
from zops.aws.cluster import Cluster


def _config_filename(filename, app_name):
    result = (
        Path(
            os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
        )
        / app_name
        / filename
    )
    print(f"ZOPS_AWS_CONFIG_FILE: {result}")
    if not result.is_file():
        print("ZOPS_AWS_CONFIG_FILE: File not found. Generating new configuration file.")
        result.parent.mkdir(parents=True, exist_ok=True)
        source_config = Path(__file__).parent / filename
        shutil.copy(source_config, result)
    return result


def load_config():
    config_filename = _config_filename("config.yml", "zops.aws")
    with open(config_filename, "r") as iss:
        config = yaml.safe_load(iss)

    Cluster.load_clusters(config["clusters"])
    Cluster.AWS_OWNERS = config["aws_owners"]
    AutoScalingGroup.PROFILE_MAP = config["aws_profiles_map"]
