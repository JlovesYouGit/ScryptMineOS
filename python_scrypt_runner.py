import pyscrypt


# python_scrypt_runner.py
# Host code for Python Scrypt implementation
def main() -> int:
    print("Starting Python Scrypt runner...")

    # Input data
    password = b"password"
    salt = b"salt"

    # Scrypt parameters
    N = EXTENDED_TIMEOUT_MS
    r = 1
    p = 1
    dkLen = 32

    # Run scrypt
    derived_key = pyscrypt.hash(password, salt, N, r, p, dkLen)

    # Print the derived key
    print(f"Derived key: {derived_key.hex()}")

    print("Python Scrypt runner finished.")


if __name__ == "__main__":
    main()
