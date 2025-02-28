# High-Performance TCP Server for Real-Time File Search and SSL Authentication

This is a multi-threaded TCP server that handles concurrent client connections and efficiently performs string searches within large files. The server is capable of reading configuration files to dynamically locate a file path and checks if a specified string exists in that file. The system is optimized for performance and includes security features like SSL authentication for encrypted communication.

## Features

- **Multi-threading Support**: Handles a large number of concurrent client requests in parallel.
- **String Search**: Searches for an exact match of a string in a file, ensuring full line matches (not partial).
- **Optimized Search**: Configurable behavior to either re-read the file on every query (`REREAD_ON_QUERY=True`) or read it once at startup (`REREAD_ON_QUERY=False`).
- **Large File Handling**: Supports large files (up to 250,000 lines) with optimized search algorithms.
- **SSL Authentication**: Secure communication between the server and client using SSL (configurable to enable/disable).
- **Logging and Debugging**: Includes detailed logging for performance monitoring, such as query strings, timestamps, and execution times.
- **Security**: Protections against buffer overflows and other potential security issues.

## Tech Stack

- ![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
- The server is implemented using Python for ease of development and performance.
- ![Nginx](https://img.shields.io/badge/Nginx-009639?style=for-the-badge&logo=nginx&logoColor=white)
- Used for load balancing and managing incoming connections.
- ![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)
- Database for configuration and logging data storage (if needed).
- **SSL/TLS**: Secure communication between clients and the server.

## Installation

To run the server as a Linux daemon or service, follow these steps:

### 1. Clone the repository

```bash
git clone https://github.com/JamesWainaina/FastSearchDaemon.git
```

```bash
cd FastSearchDaemon
```

### 2. Install dependencies

pip install -r requirements.txt

### 3. Configure the server

Modify the configuration file to specify the correct file path (e.g., linuxpath=/root/200k.txt) and configure other settings such as the SSL option.

### 4. Running the server

To start the server as a daemon or service:

```bash
python3 server.py
```

```bash
python3 client.py
```
