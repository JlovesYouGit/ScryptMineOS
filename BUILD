load("@rules_python//python:defs.bzl", "py_binary", "py_library")

# Main mining scripts
py_binary(
    name = "runner",
    srcs = ["runner.py"],
    deps = [
        ":mining_lib",
        "@scrypt_doge_deps//:jinja2",
        "@scrypt_doge_deps//:numpy",
        "@scrypt_doge_deps//:pyopencl",
    ],
)

py_binary(
    name = "asic_monitor",
    srcs = ["asic_monitor.py"],
    deps = [
        ":mining_lib",
        "@scrypt_doge_deps//:prometheus_client",
    ],
)

py_binary(
    name = "performance_optimizer",
    srcs = ["performance_optimizer.py"],
    deps = [
        ":mining_lib",
    ],
)

# Core mining library
py_library(
    name = "mining_lib",
    srcs = [
        "algo_switcher.py",
        "asic_hardware_emulation.py",
        "asic_virtualization.py",
        "asic_monitor.py",
        "autotune.py",
        "continuous_miner.py",
        "economic_config.py",
        "economic_guardian.py",
        "gpu_asic_hybrid.py",
        "performance_optimizer.py",
        "profit_switcher.py",
        "resolver.py",
        "runner.py",
        "runner_continuous.py",
    ],
    deps = [
        "@scrypt_doge_deps//:jinja2",
        "@scrypt_doge_deps//:numpy",
        "@scrypt_doge_deps//:pyopencl",
        "@scrypt_doge_deps//:requests",
        "@scrypt_doge_deps//:prometheus_client",
    ],
)

# Tests
py_binary(
    name = "test_asic_virtualization",
    srcs = ["test_asic_virtualization.py"],
    deps = [
        ":mining_lib",
    ],
)

py_binary(
    name = "test_economic_safety",
    srcs = ["test_economic_safety.py"],
    deps = [
        ":mining_lib",
    ],
)