import pyopencl as cl

# Read the combined rendered kernel
with open('test_combined_rendered.cl', 'r') as f:
    kernel_source = f.read()

# Get platform and device
platform = cl.get_platforms()[0]
device = platform.get_devices()[0]

# Create context and queue
context = cl.Context([device])
queue = cl.CommandQueue(context)

# Try to build the program
try:
    program = cl.Program(context, kernel_source).build()
    print("Combined OpenCL program built successfully!")
except cl.RuntimeError as e:
    print(f"OpenCL build error: {e}")
    # Try to get build log
    try:
        program = cl.Program(context, kernel_source)
        program.build()
    except cl.RuntimeError as build_error:
        print("Build log:")
        print(program.get_build_info(device, cl.program_build_info.LOG))