import datetime
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

import dateutil


def format_date(d):
    return d.replace(tzinfo=None).isoformat(" ", timespec="minutes") if d else ""


def parse_date(d):
    if len(d) > 10:
        return dateutil.parser.isoparse(d)
    else:
        return d


def get_resource_attr(obj, attr):
    """Returns the given resource (obj) attribute normalized.

    Formats:
      "xxx": obj.xxx
      "tag_xxx": obj.tags[Key=xxx].Value
    """
    result = ""
    if attr.startswith("tags:"):
        tag_name = attr.split(":")[-1]
        if not obj.tags:
            result = "-"
        else:
            for i_tag in obj.tags:
                if i_tag["Key"].lower() == tag_name.lower():
                    result = i_tag["Value"]
    elif ":" in attr:
        attr, key = attr.split(":")
        result = getattr(obj, attr).get(key)
    elif attr == "encrypted_volumes":
        result = ""
        for i_volume in obj.volumes.all():
            if i_volume.kms_key_id is None:
                result += "x"
            else:
                result += "."
    else:
        result = obj
        for i_attr in attr.split("."):
            try:
                result = getattr(result, i_attr)
            except AttributeError:
                result = "?"
                break
    if "creation_date" in attr:
        result = parse_date(result)
    if isinstance(result, datetime.datetime):
        result = result.strftime("%Y-%m-%d %H:%M")
    return result
