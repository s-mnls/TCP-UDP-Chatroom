# TCP UDP Chatroom

This project is a simple **UDP-based chat application** consisting of a **server** and **client**. The server can handle multiple clients concurrently, allowing them to send messages to each other. Messages are broadcasted to all connected clients, and clients can join or leave the chat at any time.

## Features

- **Server:**
  - Manages multiple client connections.
  - Broadcasts messages to all connected clients.
  - Handles client joining and leaving the chat.
  - Supports graceful server shutdown and client disconnection.

- **Client:**
  - Connects to the server with a unique username.
  - Sends and receives messages from the server.
  - Displays incoming messages and allows users to type and send their own messages.
  - Allows users to exit the chat.

## Prerequisites

- Python 3.x
- `socket` and `threading` libraries (part of Python standard library)

## How to Use

### Running the Server
1. Open the folder containing the server code.
2. Change line 6
   ```bash
   server = ServerTCP(<server_port>)
   ```
   Replace `<server_port>` with the desired port number (e.g., 12345).
   
3. Run the server using the command:
   ```bash
   python server.py
   ```

### Running the Client
1. Open another terminal for each client.
2. Run the client with the following command:
   ```bash
   python client.py --name <client_name>
   ```
   Replace `<client_name>` with the desired username

3. After connecting, clients can send messages by typing them into the terminal. Type `exit` to leave the chat.

## How It Works

- **Server:**  
  The server listens for incoming messages on a specified port. When a client connects, it sends the client's name and starts receiving and broadcasting messages. It also handles clients joining and leaving the chat.
  
- **Client:**  
  The client connects to the server using the provided IP address and port. It sends messages to the server and receives broadcasted messages from other clients. The client uses multi-threading to handle receiving messages asynchronously while allowing the user to input their own messages.

## Example

### Server Terminal
```bash
Server is listening on port 12345
```

### Client Terminal
```bash
Client 1: Hello, Server!
Client 2: Hi, Client 1!
```

## Known Issues

- The server does not support client message history or message persistence.
- The client and server do not support any kind of encryption or secure communication.
