import hashlib
import sys


def hash_api_key(api_key):
    """Hash the provided API key using SHA-256 and return the hash as a hex string."""
    try:
        hash_object = hashlib.sha256(api_key.encode())
        hex_dig = hash_object.hexdigest()
        return hex_dig
    except Exception as e:
        error_message = f"An error occurred while hashing the API key: {str(e)}"
        raise Exception(error_message)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Error: Exactly one argument must be provided for the API key.")
        print(f"Usage: python {sys.argv[0]} <api_key>")
        sys.exit(1)

    api_key = sys.argv[1]

    try:
        hashed_key = hash_api_key(api_key)
        print(f"Hashed API Key: {hashed_key}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)
