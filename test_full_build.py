import pyopencl as cl

# Read both kernel files and combine them
with open('kernels/scrypt_core.cl.jinja', 'r') as f:
    scrypt_core = f.read()

with open('test_rendered_kernel.cl', 'r') as f:
    asic_optimized = f.read()

# Combine the kernels (this is what happens in the full rendering)
full_kernel = scrypt_core + "\n" + asic_optimized

# Get platform and device
platform = cl.get_platforms()[0]
device = platform.get_devices()[0]

# Create context and queue
context = cl.Context([device])
queue = cl.CommandQueue(context)

# Try to build the program
try:
    program = cl.Program(context, full_kernel).build()
    print("Full OpenCL program built successfully!")
except cl.RuntimeError as e:
    print(f"OpenCL build error: {e}")
    # Try to get build log
    try:
        program = cl.Program(context, full_kernel)
        program.build()
    except cl.RuntimeError as build_error:
        print("Build log:")
        print(program.get_build_info(device, cl.program_build_info.LOG))