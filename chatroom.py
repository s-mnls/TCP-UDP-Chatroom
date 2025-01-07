import socket
import threading
import sys
import select


class ServerTCP:
    def __init__(self, server_port):
        self.addr = socket.gethostbyname(socket.gethostname())
        self.server_port = server_port

        # Initializes dictionary of clients
        self.clients = {}

        # Initializes TCP socket
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Initialize threading events to control server state
        self.run_event = threading.Event()
        self.handle_event = threading.Event()

        # Clear run event and handle_event to signify server is running
        self.run_event.clear()
        self.handle_event.clear()

        try:
            # Binds to local host and server port, and starts listening for messages
            self.server_socket.bind((self.addr, self.server_port))
            self.server_socket.listen(5)

        except Exception as e:
            print(f"Exception occurred: {e}")

    def accept_client(self):
        try:
            readable, _, _ = select.select([self.server_socket], [], [], 1)
            if self.server_socket in readable:
                client_socket, client_address = self.server_socket.accept()

                # States what client has been connected and receives its name
                client_name = client_socket.recv(1024).decode('utf-8')

                # If client socket is already stored in dictionary, return False
                if client_name in self.clients.values():
                    print(f"Server side: Client name already in dictionary: {client_socket.getpeername()} disconnected")
                    # Send 'Name already taken' message to the client
                    client_socket.send("Name already taken".encode('utf-8'))
                    client_socket.close()
                    return False

                else:
                    # Send welcome message to client
                    client_socket.send(f"Welcome!".encode('utf-8'))

                    # If this code runs, that means the client name is unique, and it will be stored into the dictionary
                    self.clients[client_socket] = client_name

                    # Broadcast connected to the chat to client
                    self.broadcast(client_socket, "join")

                    # Start thread for handling client
                    threading.Thread(target=self.handle_client, args=(client_socket,)).start()

                    return True
            return False
        except Exception as e:
            print(f"Server side: Error receiving client: {e}")
            return False

    def close_client(self, client_socket):
        if client_socket in self.clients:
            try:
                self.broadcast(client_socket, "exit")
                client_socket.send("exit".encode('utf-8'))
                del self.clients[client_socket]
                client_socket.close()
                return True

            except Exception as e:
                # Print error and return false if fails
                print(f"Server side: Error disconnecting client {client_socket}: {e}")
                return False
        return False

    def broadcast(self, client_socket_sent, message):
        try:
            if len(self.clients) >= 1:
                # Join message
                if message == "join":
                    # Message to be broadcast
                    message = f"\nUser {self.clients[client_socket_sent]} joined"

                    # Send message to each client, that isn't the client that joins or leaves
                    for client in self.clients:
                        if client != client_socket_sent:
                            client.send(message.encode('utf-8'))
                    print(f"Server side: Client {client_socket_sent.getpeername()} connected")

                # Leave message
                elif message == "exit":
                    # Message to be broadcast
                    message = f"\nUser {self.clients[client_socket_sent]} left"
                    # Send message to each client, that isn't the client that joins or leaves
                    for client in self.clients:
                        if client != client_socket_sent:
                            client.send(message.encode('utf-8'))
                    print(f"Server side: Client {client_socket_sent.getpeername()} disconnected")
                else:
                    print(f"Server side: ({self.clients[client_socket_sent]}): {message}")
                    for client in self.clients:
                        if client != client_socket_sent:
                            client.send(message.encode('utf-8'))

        except Exception as e:
            print(f"Server side: Error broadcasting message {message}: {e}")

    def shutdown(self):

        # Turn into list to avoid the loop stopping because the dictionary is being modified
        for client in list(self.clients.keys()):
            try:
                # Send server shutdown message to clients
                client.send("server-shutdown".encode('utf-8'))

                # Close client socket
                client.close()

                print(f"Server side: Closed connection for {self.clients[client]}")
                # Remove from dictionary
                del self.clients[client]

            except Exception as e:
                # Print message if there is an exception
                print(f"Server side: Error shutting down server {client}: {e}")

        self.run_event.set()
        self.handle_event.set()

        # Attempt to close server socket
        try:
            self.server_socket.close()
            print("Server side: Server socket closed.")
        except Exception as e:
            print(f"Server side: Error closing server socket: {e}")
            return False

        # Indicate successful shutdown
        print("Server shutdown complete.")
        return True

    def get_clients_number(self):
        return len(self.clients)

    def handle_client(self, client_socket):
        try:
            while not self.handle_event.is_set():
                readable, _, _ = select.select([client_socket], [], [], 1)  # 1-second timeout
                if readable:
                    # Decodes client message
                    message = client_socket.recv(1024).decode('utf-8')
                    if message:
                        # If client sends a message requesting to exit, run this code
                        if message.lower() == "exit":
                            print(f"Server side: Client requested to exit ({client_socket.getpeername()})")
                            self.close_client(client_socket)
                            break
                        # Broadcast received message from client
                        self.broadcast(client_socket, message)

        except OSError as e:
            pass  # Attempted handling a closed socket
        except Exception as e:
            print(f"Server side: Error handling client {client_socket}: {e}")

    def run(self):
        try:
            print(f"Server is listening on port {self.server_port}")
            while not self.run_event.is_set():
                if self.accept_client():
                    print("Server Side: Client successfully connected")

        except KeyboardInterrupt as e:
            print(f"Server Side: Server received keyboard interrupt: {e}")
        finally:
            self.run_event.set()
            self.handle_event.set()
            self.shutdown()


class ClientTCP:
    def __init__(self, client_name, server_port):
        self.server_port = server_port

        # Initialize events and variables
        self.client_name = client_name
        self.exit_run = threading.Event()
        self.exit_receive = threading.Event()

        try:
            # Find local address
            self.server_addr = socket.gethostbyname(socket.gethostname())

            # Connect client to server
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        except Exception as e:
            print(f"Client side: Error connecting client {self.client_name}: {e}")

    def connect_server(self):
        try:
            self.client_socket.connect((self.server_addr, self.server_port))
            # Upon entering the server, send the client's name to be stored in the dictionary
            self.client_socket.send(self.client_name.encode('utf-8'))

            # Check server response
            if "Welcome!" in self.client_socket.recv(1024).decode('utf-8'):
                print(f"Client side: {self.client_name} connected")
                # Send name to server
                return True
            elif "Name already taken" in self.client_socket.recv(1024).decode('utf-8'):
                print(f"Client side: {self.client_name} already taken")
                return False

        except Exception as e:
            print(f"Client side: Error connecting client {self.client_name}: {e}")
            return False

    def send(self, text):
        try:
            text = f"{self.client_name}: {text}"
            self.client_socket.send(text.encode('utf-8'))
        except Exception as e:
            print(f"\nClient side: Error sending message: {e}")

    def receive(self):
        try:
            while not self.exit_receive.is_set():
                readable, _, _ = select.select([self.client_socket], [], [], 1)  # 1-second timeout
                if readable:
                    message = self.client_socket.recv(1024).decode('utf-8')
                    if message:
                        if message.lower() == "server-shutdown":
                            print(f"\nClient side: Server shutting down")
                            break
                        elif message.lower() == "exit" or message == "Name already taken":
                            print(f"\nClient side: Client shutting down")
                            break
                        else:
                            # Clear current input prompt line and display message
                            sys.stdout.write("\r" + " " * (len(f"{self.client_name}: ") + 20) + "\r")
                            sys.stdout.write(f"{message}\n{self.client_name}: ")
                            sys.stdout.flush()
        except Exception as e:
            print(f"\nError receiving message: {e}")

    def run(self):
        try:
            if self.connect_server():
                # Start receiving messages thread
                receive_thread = threading.Thread(target=self.receive)
                receive_thread.start()
                print("(type 'exit' to quit)")

                while not self.exit_run.is_set():
                    sys.stdout.write(f"{self.client_name}: ")
                    sys.stdout.flush()
                    message = input()
                    if message.lower().strip() == "exit":
                        self.client_socket.send("exit".encode('utf-8'))
                        break
                    if message:
                        self.send(message)
                self.exit_run.set()
                self.exit_receive.set()
                receive_thread.join()
                self.client_socket.close()
            else:
                print("Connection closed.")

        except KeyboardInterrupt as e:
            print(f"\nClient side: Server received keyboard interrupt: {e}")

class ServerUDP:
    def __init__(self, server_port):
        self.server_port = server_port

        try:
            # Initialize server address and socket
            self.server_addr = (socket.gethostbyname(socket.gethostname()), self.server_port)
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.server_socket.bind(self.server_addr)

            # Initialize clients and messages
            self.clients = {}  # Dictionary to store client addresses and names
            self.messages = []  # List to store messages for broadcasting
            print(f"Server is listening on port {server_port}")

        except Exception as e:
            print(f"Server side: Error connecting server: {e}")

    def accept_client(self, client_addr, message):
        try:
            # Send welcome message to new client
            self.server_socket.sendto("Welcome".encode('utf-8'), client_addr)

            client_name, addr = self.server_socket.recvfrom(1024)
            client_name = client_name.decode('utf-8')

            # Check if client name is already in use
            if client_name in self.clients.values():
                print(f"Server Side: Name {client_name} ({client_addr}): already connected")
                self.server_socket.sendto("Name already taken".encode('utf-8'), client_addr)
                return False

            self.clients[client_addr] = client_name  # Add client to dictionary

            self.messages.append((client_addr, f"User {client_name} joined"))  # Prepare join message
            self.broadcast()  # Broadcast to other clients
            print(f"Server Side: {client_name} connected from {client_addr}")
            return True

        except Exception as e:
            print(f"Server side: Error receiving message: {e}")
            return False

    def close_client(self, client_addr):
        try:
            client_name = self.clients[client_addr]
            self.messages.append((client_addr, f"User {client_name} left the chat."))  # Prepare leave message
            self.broadcast()  # Broadcast to other clients
            print(f"Server Side: {client_name} has left the chat.")
            del self.clients[client_addr]
            return True
        except Exception as e:
            print(f"Server side: Error closing client {client_addr}: {e}")
            return False

    def broadcast(self):
        try:
            sender_addr, message = self.messages.pop(0)  # Get the latest message
            print(f"Server Side: {message}")
            for client_addr in self.clients.keys():
                if client_addr != sender_addr:  # Do not send back to the sender
                    self.server_socket.sendto(message.encode('utf-8'), client_addr)

        except Exception as e:
            print(f"Server side: Error broadcasting message: {e}")

    def shutdown(self):
        try:
            for client in list(self.clients.keys()):
                self.server_socket.sendto("server-shutdown".encode('utf-8'), client)
                self.close_client(client)  # Close the client connection
            self.server_socket.close()  # Close the server socket
        except Exception as e:
            print(f"Server side: Error closing server: {e}")

    def get_clients_number(self):
        return len(self.clients)  # Return number of connected clients

    def run(self):
        try:
            while True:
                data, client_addr = self.server_socket.recvfrom(1024)  # Receive messages
                message = data.decode('utf-8')
                if message == "join":
                    self.accept_client(client_addr, message)
                elif message.lower() == "exit":  # Client exiting
                    self.close_client(client_addr)

                elif client_addr in self.clients:  # Existing client sending a message
                    message = f"{self.clients[client_addr]}: {message}"
                    self.messages.append((client_addr, message))
                    self.broadcast()

        except KeyboardInterrupt:
            print("\nServer side: Server shutting down")
        except Exception as e:
            print(f"\nServer side: Error handling client: {e}")
        finally:
            self.shutdown()


class ClientUDP:
    def __init__(self, client_name, server_port):
        self.localAddr = socket.gethostbyname(socket.gethostname())
        self.server_port = server_port
        self.client_name = client_name

        # Set up client details
        self.server_addr = (self.localAddr, self.server_port)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Threading events to control loops
        self.exit_run = threading.Event()
        self.exit_receive = threading.Event()

    def connect_server(self):
        self.send('join')
        try:
            response, addr = self.client_socket.recvfrom(1024)

            self.client_socket.sendto(f"{self.client_name}".encode('utf-8'), addr)

            if response == 'Welcome':
                self.exit_run.set()
                self.exit_receive.set()  # Signal the receive thread to exit
                self.client_socket.close()
                return False

            print(f"Client Side: {self.client_name} successfully connected to server.")
            return True

        except Exception as e:
            print(f"Error connecting to server: {e}")
        return False

    def send(self, text):
        try:
            self.client_socket.sendto(text.encode('utf-8'), self.server_addr)
        except Exception as e:
            print(f"\nError sending message: {e}")

    def receive(self):
        while not self.exit_receive.is_set():
            try:
                data, addr = self.client_socket.recvfrom(1024)
                message = data.decode('utf-8')

                # Server shutdown handling
                if message == "server-shutdown":
                    print("Client side: Server shutting down")
                    self.exit_receive.set()
                    self.exit_run.set()
                    break
                else:
                    # Clear current input prompt line and display received message
                    sys.stdout.write("\r" + " " * (len(f"{self.client_name}: ") + 20) + "\r")
                    sys.stdout.write(f"{message}\n{self.client_name}: ")
                    sys.stdout.flush()
            except Exception as e:
                print(f"Client side: Error receiving message: {e}")

    def run(self):
        # Connect to the server first
        if self.connect_server():

            # Start a thread to handle receiving messages
            receive_thread = threading.Thread(target=self.receive)
            receive_thread.start()

            print("(type 'exit' to quit)")
            while not self.exit_run.is_set():
                try:
                    sys.stdout.write(f"{self.client_name}: ")
                    sys.stdout.flush()
                    message = input()
                    if message.lower().strip() == "exit":
                        self.send("exit")  # Notify server of exit
                        break
                    self.send(message)  # Send message to server
                except KeyboardInterrupt as e:
                    print(f"\nClient side: Error running client: {e}")
                    break
            self.exit_run.set()
            self.exit_receive.set()  # Signal the receive thread to exit
            self.client_socket.close()
            receive_thread.join()  # Wait for the receiving thread to finish
        print("\nDisconnected from server.")
