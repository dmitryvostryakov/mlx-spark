#!/usr/bin/env python3
"""Validate replayable, anonymized FND-02 inventory and budget evidence."""

import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "runs" / "fnd-02"
SELF_LOG = "evidence/runs/fnd-02/evidence-validation-final.stdout.log"
FORBIDDEN_KEYS = {"hostname", "ip", "mac", "uuid", "serial", "username"}
EXPECTED_INVENTORY_ARGV = [
    "bash",
    "-c",
    "ssh -o BatchMode=yes -o ConnectTimeout=10 dgx2 python3 - < src/mlx_spark/runtime/doctor.py",
]


def _load(name):
    return json.loads((EVIDENCE / name).read_text())


def _keys(value):
    if isinstance(value, dict):
        for key, item in value.items():
            yield key.lower()
            yield from _keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _keys(item)


def _require(condition, reason):
    if not condition:
        raise ValueError(reason)


def main():
    inventory = _load("inventory.json")
    budget = _load("resource-budget.json")
    run = _load("run.json")
    connectivity = _load("connectivity.json")

    rendered_inventory = json.dumps(inventory)
    _require(not (FORBIDDEN_KEYS & set(_keys(inventory))), "forbidden_inventory_key")
    _require("/home/" not in rendered_inventory and "/Users/" not in rendered_inventory, "private_path")
    _require(re.search(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)", rendered_inventory) is None, "ip_value")
    _require(re.search(r"GPU-[0-9A-Fa-f-]{8,}", rendered_inventory) is None, "gpu_uuid")
    _require(inventory["system"] == "Linux" and inventory["machine"] == "aarch64", "architecture")
    _require(inventory["gpu"]["visible_count"] == 1, "visible_gpu_count")
    device = inventory["gpu"]["devices"][0]
    _require(device["name"] == "NVIDIA GB10" and device["compute_capability"] == "12.1", "gpu_target")

    memory = budget["memory"]
    disk = budget["disk"]
    _require(memory["effective_available_bytes"] == inventory["memory"]["MemAvailable_bytes"], "memory_basis")
    _require(
        memory["project_working_set_cap_bytes"] + memory["system_reserve_bytes"]
        <= memory["effective_available_bytes"],
        "memory_reserve",
    )
    _require(
        disk["project_total_cap_bytes"] + disk["minimum_free_floor_bytes"] <= disk["observed_free_bytes"],
        "disk_floor",
    )
    _require(disk["build_cache_cap_bytes"] <= disk["project_total_cap_bytes"], "build_cache_cap")
    _require(budget["weights_download_authorized"] is False, "weights_authorization")

    inventory_commands = [command for command in run["commands"] if command["log_path"].endswith("inventory.json")]
    _require(len(inventory_commands) == 1, "inventory_command_count")
    _require(inventory_commands[0]["argv"] == EXPECTED_INVENTORY_ARGV, "inventory_argv")
    _require(inventory_commands[0]["exit_code"] == 0, "inventory_exit")
    _require(run["hardware"]["hardware_validation"] == "READ_ONLY_INVENTORY_ONLY", "hardware_claim")
    _require(run["hardware"]["cuda_execution_validation"] == "NOT_PERFORMED", "cuda_claim")
    _require(run["toolchain"]["cuda_toolkit"]["status"] == "unknown", "cuda_toolkit_unknown")
    _require(run["toolchain"]["cudnn"]["status"] == "unknown", "cudnn_unknown")
    _require(connectivity["scope_guards"]["second_node_contacted"] is False, "second_node")
    _require(connectivity["scope_guards"]["tp2_touched"] is False, "tp2")

    command_text = " ".join(argument.lower() for command in run["commands"] for argument in command["argv"])
    _require("require zero matches" not in command_text, "descriptive_pseudo_command")
    _require(not any(term in command_text for term in ("dgx1", " nccl", " qsfp", " tp2")), "scope_command")
    missing_logs = [
        command["log_path"]
        for command in run["commands"]
        if command["log_path"] != SELF_LOG and not (ROOT / command["log_path"]).is_file()
    ]
    _require(not missing_logs, "missing_referenced_log")

    print(
        json.dumps(
            {
                "budget": "valid",
                "inventory": "valid",
                "privacy": "valid",
                "referenced_logs": "all_present",
                "run": "valid",
                "scope": "single_spark",
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
