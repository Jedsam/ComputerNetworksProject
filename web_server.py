import socket
import threading
import sys

def handle_client(connection, address):
    print(f"Connection from {address}")

    try:
        request = connection.recv(1024).decode()
        print(f"Received request:\n{request}")

        # Parse the request
        lines = request.splitlines()
        if len(lines) == 0:
            return

        request_line = lines[0]
        parts = request_line.split()
        if len(parts) != 3:
            # Bad Request
            response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
            connection.sendall(response.encode())
            print(f"Sent response:\n{response}")
            return

        method, uri, version = parts

        if method != "GET":
            # Check if method is a valid HTTP method
            valid_methods = ["POST", "PUT", "DELETE", "HEAD", "OPTIONS", "TRACE", "CONNECT"]
            if method in valid_methods:
                # Not Implemented
                response = "HTTP/1.0 501 Not Implemented\r\n\r\nNot Implemented"
                connection.sendall(response.encode())
                print(f"Sent response:\n{response}")
                return
            else:
                # Bad Request
                response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
                connection.sendall(response.encode())
                print(f"Sent response:\n{response}")
                return

        # Remove leading slash '/'
        if uri.startswith('/'):
            uri = uri[1:]

        # Extract size
        try:
            size = int(uri)
            if size < 100 or size > 20000:
                # Bad Request
                response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
                connection.sendall(response.encode())
                print(f"Sent response:\n{response}")
                return
        except ValueError:
            # URI is not an integer
            response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
            connection.sendall(response.encode())
            print(f"Sent response:\n{response}")
            return

        # Generate the HTML document with the specified size
        # Build a basic HTML structure
        html = "<HTML>\n<HEAD>\n<TITLE>I am {} bytes long</TITLE>\n</HEAD>\n<BODY>\n".format(size)
        current_length = len(html) + len("</BODY>\n</HTML>\n")
        # Fill the body with content to reach the desired size
        content_size = size - current_length
        if content_size < 0:
            # Can't generate HTML of that size
            response = "HTTP/1.0 400 Bad Request\r\n\r\nBad Request"
            connection.sendall(response.encode())
            print(f"Sent response:\n{response}")
            return

        # We can fill the body with any character, here we use 'a'
        body_content = 'a' * content_size
        html += body_content
        html += "\n</BODY>\n</HTML>\n"

        # Prepare the HTTP response
        response_line = "HTTP/1.0 200 OK\r\n"
        headers = "Content-Type: text/html\r\n"
        headers += "Content-Length: {}\r\n".format(len(html))
        response = response_line + headers + "\r\n" + html

        connection.sendall(response.encode())
        print(f"Sent response:\n{response}")
    finally:
        connection.close()
        print(f"Connection closed with {address}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python web_server.py <port>")
        sys.exit(1)

    port = int(sys.argv[1])

    # Create socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow reusing the socket
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # Bind to the specified port
    server_socket.bind(('', port))
    # Listen for connections
    server_socket.listen(5)
    print(f"Server listening on port {port}")

    while True:
        # Accept a client connection
        client_connection, client_address = server_socket.accept()
        # Create a new thread to handle the client
        client_thread = threading.Thread(target=handle_client, args=(client_connection, client_address))
        client_thread.start()

if __name__ == '__main__':
    main()
