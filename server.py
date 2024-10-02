#!/usr/bin/python3

import socket
import ssl
import logging
import signal
import sys
from configparser import ConfigParser
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable for server socket
server_ssl: ssl.SSLSocket | None = None

def signal_handler(sig: int, frame) -> None:
    """Handle termination signals gracefully."""
    global server_ssl
    logger.info("Signal received, shutting down the server gracefully.")
    if server_ssl:
        server_ssl.close()
    sys.exit(0)

def run_server() -> None:
    """Run the SSL server."""
    global server_ssl 

    # Create a socket object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    config_path = "config.init"
    linuxpath, reread_on_query = read_config(config_path)

    if linuxpath is None:
        logger.error("No 'linuxpath' found in the configuration file")
        return

    server_ip = "127.0.0.1"
    port = 8000

    # Bind the socket to a specific address and port
    server.bind((server_ip, port))
    server.listen(5)  # Allow multiple connections
    logger.info(f"Listening on {server_ip}:{port}")

    # Create an SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ssl_context.load_cert_chain(certfile="server.crt", keyfile="server.key")

    # Wrap the socket with SSL
    server_ssl = ssl_context.wrap_socket(server, server_side=True)

    with ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            try:
                # Accept incoming connections
                client_socket, client_address = server_ssl.accept()
                logger.info(f"Accepted connection from {client_address[0]}:{client_address[1]}")

                # Handle the client connection
                executor.submit(handle_client, client_socket, linuxpath, reread_on_query)

            except Exception as e:
                logger.error(f"Error while handling client: {e}")
                continue

def handle_client(client_socket: socket.socket, linux_path: Path, reread_on_query: bool) -> None:
    """Handles client communication."""
    with client_socket:
        while True:
            request = client_socket.recv(1024).decode("utf-8").strip()  # Convert bytes to string and strip whitespace

            # If we receive "close" from the client, then we break out of the loop
            if request.lower() == "close":
                client_socket.send("closed".encode("utf-8"))
                break

            logger.info(f"Received: {request}")

            # Check if the search string exists in the file
            response = check_string_file(linux_path, request, reread_on_query)
            client_socket.send(response.encode("utf-8"))

    logger.info("Connection to client closed")

def read_config(file_path: str) -> tuple[Path | None, bool]:
    """Reads the configuration file and returns the linux path and reread option."""
    config = ConfigParser()
    config.read(file_path)

    # Check if 'DEFAULT' section is present in the configuration file
    if 'DEFAULT' in config:
        linuxpath = config['DEFAULT'].get('linuxpath', None)
        reread_on_query = config['DEFAULT'].getboolean('REREAD_ON_QUERY', fallback=False)
        if linuxpath is not None:
            return Path(linuxpath).resolve(), reread_on_query  # Return both values
    else:
        logger.error("No 'DEFAULT' section found in the configuration file")
    return None, False  # Return default values if not found

def check_string_file(file_path: Path, search_string: str, reread_on_query: bool) -> str:
    """Checks if the search string is present in the file."""
    file_content_cache: str | None = None  # To cache the file content

    try:
        if reread_on_query:
            # If reread_on_query is set to True, read the file content every time
            result = subprocess.run(
                ['grep', '-Fq', search_string, str(file_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            # Check if the grep command was successful
            return "STRING EXISTS\n" if result.returncode == 0 else "STRING NOT FOUND\n"
        else:
            # If reread_on_query is False, check in the cache
            if file_content_cache is None:
                # Read the file for the first time
                with open(file_path, 'r') as file:
                    file_content_cache = file.read()

            # Check if the search string is in the cached content
            return "STRING EXISTS\n" if search_string in file_content_cache else "STRING NOT FOUND\n"

    except FileNotFoundError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return "ERROR\n"
    except Exception as e:
        logger.error(f"Error executing grep: {e}")
        return "ERROR\n"

if __name__ == "__main__":
    # Set up signal handling for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle termination signal
    run_server()
