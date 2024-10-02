#!/usr/bin/python3

import socket
import ssl
import logging
import signal
import sys
from configparser import ConfigParser, NoOptionError, NoSectionError
from pathlib import Path
import subprocess
from concurrent.futures import ThreadPoolExecutor
# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Global variable for server socket
server_ssl = None

def signal_handler(sig, frame):
    """Handle termination signals gracefully."""
    global server_ssl
    logger.info("Signal received, shutting down the server gracefully.")
    if server_ssl:
        server_ssl.close()
    sys.exit(0)

def run_server():
    global server_ssl 

    # Create a socket object
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    config_path = "config.init"
    linuxpath = read_config(config_path)

    if linuxpath is None:
        logger.error("No 'linuxpath' found in the configuration file")
        return

    server_ip = "127.0.0.1"
    port = 8000

    # Bind the socket to a specific address and port
    server.bind((server_ip, port))
    # Listen for incoming connections
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
                executor.submit(handle_client, client_socket, linuxpath)

            except Exception as e:
                logger.error(f"Error while handling client: {e}")
                continue

def handle_client(client_socket, linux_path):
    """Handles client communication."""
    with client_socket:
        while True:
            request = client_socket.recv(1024)
            request = request.decode("utf-8").strip()  # Convert bytes to string and strip whitespace

            # If we receive "close" from the client, then we break out of the loop
            if request.lower() == "close":
                client_socket.send("closed".encode("utf-8"))
                break

            logger.info(f"Received: {request}")

            # Check if the search string exists in the file
            response = check_string_file(linux_path, request)
            client_socket.send(response.encode("utf-8"))

    logger.info("Connection to client closed")

def read_config(file_path):
    """Reads the configuration file and returns the linux path."""
    config = ConfigParser()
    config.read(file_path)

    # Check if 'DEFAULT' section is present in the configuration file
    if 'DEFAULT' in config:
        linuxpath = config['DEFAULT'].get('linuxpath', None)
        if linuxpath is not None:
            return Path(linuxpath).resolve()  # Resolve to an absolute path
    else:
        logger.error("No 'DEFAULT' section found in the configuration file")
    return None

def check_string_file(file_path, search_string):
    """Checks if the search string is present in the file."""
    try:
        # use grep to search for the string
        result = subprocess.run(
            ['grep', '-Fq', search_string, str(file_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        # check if the grep command was successful
        if result.returncode == 0: 
            return "STRING EXISTS\n"
        else:
            return "STRING NOT FOUND\n"
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
