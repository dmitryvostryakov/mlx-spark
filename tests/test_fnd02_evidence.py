import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence" / "runs" / "fnd-02"
GIB = 1024**3


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


def test_selected_dgx2_inventory_is_anonymized_and_single_gpu():
    inventory = _load("inventory.json")
    assert inventory["system"] == "Linux"
    assert inventory["machine"] == "aarch64"
    assert inventory["dgx_os"]["status"] == "ok"
    assert inventory["gpu"]["status"] == "ok"
    assert inventory["gpu"]["visible_count"] == 1
    assert inventory["gpu"]["devices"][0]["name"] == "NVIDIA GB10"
    assert inventory["gpu"]["devices"][0]["compute_capability"] == "12.1"
    assert not ({"hostname", "ip", "mac", "uuid", "serial", "username"} & set(_keys(inventory)))
    rendered = json.dumps(inventory)
    assert "/home/" not in rendered
    assert "/Users/" not in rendered


def test_resource_budget_preserves_memory_and_disk_reserves():
    inventory = _load("inventory.json")
    budget = _load("resource-budget.json")
    memory = budget["memory"]
    disk = budget["disk"]

    assert budget["selected_spark_label"] == "DGX2"
    assert budget["scope"] == "single_spark_foundation_only"
    assert budget["weights_download_authorized"] is False
    assert memory["effective_available_bytes"] == inventory["memory"]["MemAvailable_bytes"]
    assert memory["project_working_set_cap_bytes"] <= (
        memory["effective_available_bytes"] - memory["system_reserve_bytes"]
    )
    assert memory["system_reserve_bytes"] >= 32 * GIB
    assert memory["project_working_set_cap_bytes"] <= 80 * GIB
    assert disk["observed_free_bytes"] == inventory["disk"]["free_bytes"]
    assert disk["project_total_cap_bytes"] <= disk["observed_free_bytes"] - disk["minimum_free_floor_bytes"]
    assert disk["build_cache_cap_bytes"] <= disk["project_total_cap_bytes"]
    assert budget["guards"]["recheck_before_large_allocation_or_download"] is True
    assert budget["guards"]["automatic_system_tuning"] is False
    assert budget["guards"]["automatic_cache_prune"] is False


def test_run_records_replayable_single_node_safety_boundaries():
    run = _load("run.json")
    connectivity = _load("connectivity.json")
    expected_inventory_argv = [
        "bash",
        "-c",
        "ssh -o BatchMode=yes -o ConnectTimeout=10 dgx2 python3 - < src/mlx_spark/runtime/doctor.py",
    ]

    inventory_commands = [
        command for command in run["commands"] if command["log_path"] == "evidence/runs/fnd-02/inventory.json"
    ]
    assert len(inventory_commands) == 1
    assert inventory_commands[0]["argv"] == expected_inventory_argv
    assert inventory_commands[0]["exit_code"] == 0
    assert run["hardware"]["hardware_validation"] == "READ_ONLY_INVENTORY_ONLY"
    assert run["hardware"]["cuda_execution_validation"] == "NOT_PERFORMED"
    assert run["toolchain"]["driver"] == "580.159.03"
    assert run["toolchain"]["host_compiler"] == "gcc 13.3.0"
    assert run["toolchain"]["cuda_toolkit"]["status"] == "unknown"
    assert run["toolchain"]["cudnn"]["status"] == "unknown"
    assert connectivity["scope_guards"]["second_node_contacted"] is False
    assert connectivity["scope_guards"]["tp2_touched"] is False
    assert any("TP2" in item for item in run["unrun"])
    assert all(
        "require zero matches" not in argument
        for command in run["commands"]
        for argument in command["argv"]
    )
    assert all((ROOT / command["log_path"]).is_file() for command in run["commands"])


def test_fnd02_validator_is_replayable():
    process = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "validate_fnd02_evidence.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode == 0, process.stderr
    result = json.loads(process.stdout)
    assert result["inventory"] == "valid"
    assert result["budget"] == "valid"
    assert result["privacy"] == "valid"
    assert result["scope"] == "single_spark"
