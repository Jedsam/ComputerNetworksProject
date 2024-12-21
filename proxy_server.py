import socket
import threading

def handle_client(client_connection, client_address):
    print(f"Connection from {client_address}")

    try:
        request = client_connection.recv(4096).decode()
        print(f"Received request from client:\n{request}")

        # Parse the request
        lines = request.splitlines()
        if len(lines) == 0:
            return

        request_line = lines[0]
        parts = request_line.split()
        if len(parts) < 3:
            # Bad Request
            response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
            client_connection.sendall(response.encode())
            print(f"Sent response to client:\n{response}")
            return

        method, uri, version = parts

        # Extract the requested file size from the URI
        # The URI can be absolute (http://localhost:8080/500) or relative (/500)
        if uri.startswith("http://"):
            # Absolute URI
            # Parse the path
            uri_parts = uri[7:]  # Remove 'http://'
            host_port_and_path = uri_parts.split('/', 1)
            host_port = host_port_and_path[0]
            path = '/' + host_port_and_path[1] if len(host_port_and_path) > 1 else '/'
            # Enforce that the host and port are localhost:8080
            host = 'localhost'
            port = 8080
        else:
            # Relative URI
            host = 'localhost'
            port = 8080  # Default web server port
            path = uri

        # Now, extract the size from the path
        if path.startswith('/'):
            size_str = path[1:]
        else:
            size_str = path

        try:
            size = int(size_str)
            if size > 9999:
                # Request-URI Too Long
                response = "HTTP/1.0 414 Request-URI Too Long\r\n\r\nRequest-URI Too Long"
                client_connection.sendall(response.encode())
                print(f"Sent response to client:\n{response}")
                return
        except ValueError:
            # Bad Request
            response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
            client_connection.sendall(response.encode())
            print(f"Sent response to client:\n{response}")
            return

        # Forward the request to the web server
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            server_socket.connect((host, port))

            # Build the request to the web server
            server_request_line = f"{method} {path} {version}\r\n"
            # Add Host header
            headers = f"Host: {host}:{port}\r\n"

            # Collect additional headers from client request
            client_headers = ''
            header_lines = []
            header_started = False
            for line in lines[1:]:
                if line == '':
                    header_started = True
                    continue
                if not header_started:
                    header_lines.append(line)
                else:
                    break
            client_headers = '\r\n'.join(header_lines)

            server_request = server_request_line + headers + client_headers + '\r\n\r\n'

            print(f"Forwarding request to web server:\n{server_request}")
            server_socket.sendall(server_request.encode())

            # Receive the response from the web server and send back to client
            while True:
                data = server_socket.recv(4096)
                if not data:
                    break
                client_connection.sendall(data)
            print(f"Response forwarded to client.")

        except socket.error as e:
            # Web server not running
            client_response = "HTTP/1.0 404 Not Found\r\n\r\nNot Found"
            client_connection.sendall(client_response.encode())
            print(f"Sent response to client:\n{client_response}")
        finally:
            server_socket.close()

    finally:
        client_connection.close()
        print(f"Connection closed with {client_address}")

def main():
    # Proxy server listens on port 8888
    port = 8888

    # Create socket
    proxy_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reusing the socket
    proxy_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to port 8888
    proxy_socket.bind(('', port))
    # Listen for connections
    proxy_socket.listen(5)
    print(f"Proxy server listening on port {port}")

    while True:
        # Accept a client connection
        client_connection, client_address = proxy_socket.accept()
        # Create a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_connection, client_address))
        client_thread.start()

if __name__ == '__main__':
    main()
