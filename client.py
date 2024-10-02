import socket
import ssl

def run_client():
    # Create a socket object
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    server_ip = "127.0.0.1"  # Replace with the server's IP address
    server_port = 8000  # Replace with the server's port number

    # Create an SSL context
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    
    # Load the server's certificate for validation
    ssl_context.load_verify_locations(cafile="server.crt")

    # Wrap the socket with SSL, providing the server_hostname
    client_ssl = ssl_context.wrap_socket(client, server_hostname=server_ip)

    # Establish connection with server
    client_ssl.connect((server_ip, server_port))

    while True:
        # Input message and send it to the server
        msg = input("Enter message: ")
        client_ssl.send(msg.encode("utf-8")[:1024])

        # Receive message from the server
        response = client_ssl.recv(1024)
        response = response.decode("utf-8")

        # If server sent us "closed" in the payload, we break out of the loop and close our socket
        if response.lower() == "closed":
            break

        print(f"Received: {response}")

    # Close client socket (connection to the server)
    client_ssl.close()
    print("Connection to server closed")

run_client()
