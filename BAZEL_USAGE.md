# Using Bazel with scrypt_doge

This document explains how to use Bazel to build and run the scrypt_doge mining project.

## Prerequisites

1. Install Bazel: https://docs.bazel.build/versions/main/install.html
2. Python 3.10 or higher
3. All dependencies listed in `requirements.txt`

## Project Structure

The Bazel setup organizes the project into the following packages:
- `//` - Root package containing main Python scripts
- `//kernels` - OpenCL kernel files
- `//src` - C source files and OpenCL compute shaders
- `//params` - Configuration parameter files

## Building the Project

To build all targets in the project:

```bash
bazel build //...
```

To build a specific target:

```bash
bazel build //:runner
```

## Running the Miner

To run the main mining script:

```bash
bazel run //:runner
```

To run with specific arguments:

```bash
bazel run //:runner -- --help
```

## Running Tests

To run all tests:

```bash
bazel test //...
```

To run a specific test:

```bash
bazel run //:test_asic_virtualization
```

## Available Targets

### Main Scripts
- `//:runner` - Main mining script
- `//:asic_monitor` - ASIC monitoring tool
- `//:performance_optimizer` - Performance optimization tool

### Tests
- `//:test_asic_virtualization` - ASIC virtualization tests
- `//:test_economic_safety` - Economic safety tests

### Libraries
- `//:mining_lib` - Core mining library containing shared modules

### File Groups
- `//kernels:opencl_kernels` - OpenCL kernel files
- `//src:c_sources` - C source files
- `//src:opencl_sources` - OpenCL compute shaders
- `//params:params` - Configuration parameter files

## Development Workflow

1. Make changes to source files
2. Build with `bazel build //...`
3. Run tests with `bazel test //...`
4. Run the miner with `bazel run //:runner`

## Troubleshooting

### Missing Dependencies
If you encounter dependency issues, try:

```bash
pip install -r requirements.txt
```

### Cache Issues
To clean Bazel cache:

```bash
bazel clean
```

### Python Path Issues
Ensure your Python environment is activated and contains all required dependencies.