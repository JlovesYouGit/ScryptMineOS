# enhanced_runner.py
# Host code to load, compile, and run the OpenCL kernel with enhanced Stratum client.

import jinja2
import numpy as np
import time
import sys
import argparse
import traceback

# Try to import PyOpenCL
try:
    import pyopencl as cl
    print("PyOpenCL imported successfully.")
except ImportError:
    print("Error: PyOpenCL could not be imported.")
    print("Please ensure PyOpenCL is installed correctly.")
    exit()

# Import the enhanced Stratum client
from enhanced_stratum_client import EnhancedStratumClient, construct_block_header, sha256d

# --- Mining Pool Configuration (Placeholder) ---
POOL_HOST = "doge.zsolo.bid"
POOL_PORT = 8057
POOL_USER = os.getenv("POOL_USER", os.getenv("POOL_USER", os.getenv("POOL_USER", "your_wallet_address.worker_name")))
POOL_PASS = "x"

def main():
    try:  # General error handling for the entire main function
        # Redirect stderr to a log file
        sys.stderr = open("miner_error.log", "a")
        print("Starting Enhanced OpenCL runner...")

        # Parse command-line arguments for pool configuration
        parser = argparse.ArgumentParser(description="Enhanced Dogecoin Scrypt OpenCL Miner")
        parser.add_argument("--pool-host", type=str, default=POOL_HOST,
                            help="Mining pool hostname or IP address")
        parser.add_argument("--pool-port", type=int, default=POOL_PORT,
                            help="Mining pool port")
        parser.add_argument("--pool-user", type=str, default=POOL_USER,
                            help="Mining pool username (wallet address.worker_name)")
        parser.add_argument("--pool-pass", type=str, default=POOL_PASS,
                            help="Mining pool password (usually 'x')")
        args = parser.parse_args()

        # Use arguments, falling back to hardcoded defaults if not provided
        pool_host = args.pool_host
        pool_port = args.pool_port
        pool_user = args.pool_user
        pool_pass = args.pool_pass

        # 0. Initialize OpenCL
        try:
            platform = cl.get_platforms()[0]
            device = cl.get_platforms()[0].get_devices()[0]
            context = cl.Context([device])
            queue = cl.CommandQueue(context)
            print(f"OpenCL initialized with device: {device.name}")
        except Exception as e:
            print(f"Error initializing OpenCL: {e}")
            print("Please ensure OpenCL drivers are installed and a compatible device is available.")
            return

        # 0.1 Initialize Enhanced Stratum Client
        client = EnhancedStratumClient(pool_host, pool_port, pool_user, pool_pass)
        if not client.connect():
            return
        if not client.subscribe_and_authorize():
            return

        # 1. Load and render the Jinja2 template
        try:
            template_loader = jinja2.FileSystemLoader(searchpath="N:/miner/NBMiner_42.3_Win/scrypt/scrypt_doge/kernels")
            template_env = jinja2.Environment(loader=template_loader)
            template = template_env.get_template("scrypt_core.cl.jinja")
        except jinja2.exceptions.TemplateNotFound as e:
            print(f"Error loading kernel template: {e}")
            print("Please ensure the file 'kernels/scrypt_core.cl.jinja' exists.")
            return

        # Get parameters from scrypt_doge.toml (or use defaults for now)
        params = {
            'unroll': 8,
            'vector_width': 4,
            'tile_bytes': 131072
        }
        
        rendered_kernel = template.render(**params)
        print("--- Rendered Kernel (first 200 chars) ---")
        print(rendered_kernel[:200])
        print("------------------------------------\n")

        # 2. Create and build the OpenCL program
        try:
            program = cl.Program(context, rendered_kernel).build()
        except cl.LogicError as e:
            print("OpenCL Program Build Error:")
            print(e)
            if hasattr(e, 'build_log') and context.devices:
                for device in context.devices:
                    print(f"Build log for device {device.name}:")
                    print(e.build_log.get(device, 'No build log available'))
            return  # Use return instead of exit() to allow main() to finish gracefully

        # 3. Prepare data and launch kernel
        print("Listening for mining jobs...")

        # Main mining loop
        while True:
            try:
                message = client.receive_message()
                if message:
                    if message.get("method"):
                        # Handle notifications (mining.notify, mining.set_difficulty, etc.)
                        client.handle_notification(message)
                        if client.job_id:  # If a new job was set by handle_notification
                            # Use client's extranonce2_int and kernel_nonce, which are reset by handle_notification if clean_jobs is true
                            extranonce2_bytes = client.extranonce2_int.to_bytes(client.extranonce2_size, 'little')

                            # Construct the real block header
                            input_data = construct_block_header(
                                job_params=message["params"],  # Pass the full params from mining.notify
                                extranonce1=client.extranonce1,
                                extranonce2_bytes=extranonce2_bytes,
                                kernel_nonce=client.kernel_nonce  # The kernel's nonce will be part of the header
                            )

                            # Ensure input_data is 80 bytes
                            if len(input_data) != 80:
                                print(f"Error: Constructed block header is not 80 bytes! Length: {len(input_data)}")
                                continue  # Skip this job

                            # Create GPU buffers (re-create if input_data size changes, though it should be fixed at 80 bytes)
                            mf = cl.mem_flags
                            input_buf = cl.Buffer(context, mf.READ_ONLY | mf.COPY_HOST_PTR, hostbuf=input_data)
                            output_buf = cl.Buffer(context, mf.WRITE_ONLY, 32)  # Output is 32 bytes (hash)
                            v_buf = cl.Buffer(context, mf.READ_WRITE, 131072)  # Scrypt V buffer

                            # Get the kernel function
                            scrypt_kernel = program.scrypt_kernel

                            # Define global and local work sizes
                            global_size = (1,)  # One work-item for now
                            local_size = None  # Let OpenCL choose

                            # --- Mining Loop for current job ---
                            # This loop will iterate through nonces for the current job
                            # until a share is found or a new job is received.
                            max_nonces_per_job = 10000  # Limit for testing
                            current_nonce_attempt = 0

                            while True:  # Loop indefinitely for nonces and extranonce2
                                try:
                                    event = scrypt_kernel(queue, global_size, local_size, input_buf, output_buf, client.kernel_nonce, v_buf)
                                    event.wait()  # Wait for kernel to complete

                                    # Read output data (hash)
                                    output_hash_bytes = np.empty(32, dtype=np.uint8)
                                    cl.enqueue_copy(queue, output_hash_bytes, output_buf).wait()
                                    output_hash_hex = output_hash_bytes.tobytes().hex()

                                    print(f"Job ID: {client.job_id}, Nonce: {client.kernel_nonce}, Hash: {output_hash_hex}")

                                    # --- Share Validation and Submission ---
                                    # Convert target from hex string to big-endian integer
                                    # Stratum target is usually little-endian hex, so reverse it for big-endian int conversion
                                    target_bytes = bytes.fromhex(client.target)[::-1]
                                    target_int = int.from_bytes(target_bytes, 'big')

                                    # Convert output hash from kernel to big-endian integer
                                    # The output_hash_bytes is already in little-endian from the kernel, so reverse for big-endian int conversion
                                    hash_int = int.from_bytes(output_hash_bytes[::-1], 'big')

                                    if hash_int <= target_int:
                                        print(f"!!! SHARE FOUND !!! Hash: {output_hash_hex}, Target: {client.target}")
                                        # Submit share
                                        # extranonce2_hex needs to be the hex representation of extranonce2_int
                                        # ntime needs to be the ntime from the job (job_params[7])
                                        client.submit_share(
                                            extranonce2=client.extranonce2_int.to_bytes(client.extranonce2_size, 'little').hex(),
                                            ntime=message["params"][7],  # ntime from the job
                                            nonce=client.kernel_nonce.item(),  # Convert numpy uint32 to Python int
                                            hash_result=output_hash_hex  # Hash from kernel
                                        )
                                        # After finding a share, you might want to break from the inner loop
                                        # and wait for a new job, or continue mining if the pool allows.
                                        # For now, we'll continue to increment nonce.

                                    # Increment nonce for next iteration
                                    client.kernel_nonce = np.uint32(client.kernel_nonce + 1)
                                    current_nonce_attempt += 1

                                    # If we've exhausted the nonce space for this extranonce2, increment extranonce2
                                    if current_nonce_attempt >= max_nonces_per_job:
                                        client.extranonce2_int += 1
                                        # Check if extranonce2 overflows its allocated size
                                        if client.extranonce2_int >= (1 << (client.extranonce2_size * 8)):
                                            print("Extranonce2 exhausted for this job. Waiting for new job...")
                                            break  # Break from inner loop to wait for new job
                                        extranonce2_bytes = client.extranonce2_int.to_bytes(client.extranonce2_size, 'little')
                                        client.kernel_nonce = np.uint32(0)  # Reset nonce for new extranonce2
                                        current_nonce_attempt = 0  # Reset nonce attempt counter

                                        # Reconstruct input_data with new extranonce2
                                        input_data = construct_block_header(
                                            job_params=message["params"],
                                            extranonce1=client.extranonce1,
                                            extranonce2_bytes=extranonce2_bytes,
                                            kernel_nonce=client.kernel_nonce  # Start with 0 nonce for new extranonce2
                                        )
                                        # Update input_buf with new input_data
                                        cl.enqueue_copy(queue, input_buf, input_data).wait()

                                except cl.LogicError as e:
                                    print(f"Error launching kernel: {e}")
                                    break  # Break from inner mining loop on kernel error
                                except Exception as e:
                                    print(f"An error occurred during kernel execution: {e}")
                                    break  # Break from inner mining loop on other errors
                    else:
                        # Handle responses to sent messages (e.g., authorization response)
                        print(f"Received response: {message}")
                else:
                    # No message received, perhaps a timeout or connection closed
                    print("No message from pool. Reconnecting...")
                    client.sock.close()
                    if not client.connect() or not client.subscribe_and_authorize():
                        print("Failed to reconnect. Exiting.")
                        return
                    time.sleep(5)  # Wait before retrying to prevent rapid-fire errors

            except Exception as e:
                print(f"An unexpected error occurred in main mining loop: {e}")
                traceback.print_exc()  # Print full traceback for debugging
                break

    except Exception as e:
        print(f"An unexpected error occurred in main(): {e}")
        traceback.print_exc()  # Print full traceback for debugging
    finally:
        # Restore stderr and close the log file
        if sys.stderr != sys.__stderr__:
            sys.stderr.close()
            sys.stderr = sys.__stderr__

        # Print final statistics
        try:
            stats = client.get_stats()
            print("\n=== Mining Session Statistics ===")
            conn_stats = stats['connection']
            print(f"Runtime: {conn_stats['runtime_seconds']:.2f} seconds")
            print(f"Connection attempts: {conn_stats['connection']['attempts']}")
            print(f"Successful connections: {conn_stats['connection']['successful']}")
            print(f"Uptime: {conn_stats['connection']['uptime_percentage']:.2f}%")
            print(f"Shares accepted: {conn_stats['shares']['accepted']}")
            print(f"Shares rejected: {conn_stats['shares']['rejected']}")
            print(f"Share acceptance rate: {conn_stats['shares']['acceptance_rate']:.2%}")
            print(f"Hashrate: {conn_stats['performance']['hashes_per_second']:.2f} H/s")
        except:
            pass


if __name__ == "__main__":
    main()