import socket
import random
from datetime import datetime

class udp_socket:

    def __init__(self,server_ip,server_port) -> None:
        self.server_ip= server_ip
        self.server_port=server_port

    def receive(self, ip: str, port: int, server_answer: str, buffersize: int) -> bytes:
        # Create UDP socket
        UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        # Bind the socket to the specified IP address and port
        UDPServerSocket.bind((ip, port))
        print("[*] Server UDP is listening on %s:%d" % (ip, port))
        
        # Listen for incoming datagrams
        while True:
            # Receive a message
            message, client_address = UDPServerSocket.recvfrom(buffersize)
            #print("Received message from client:", message)

            # Send the server answer to the client
            UDPServerSocket.sendto(server_answer.encode(), client_address)
            
            # Return the received message
            return message, client_address
            
        # Close the socket
        UDPServerSocket.close()

    def send(self, ip: str, port: int, message: str, buffersize: int) -> str:
        # Create a UDP socket at client side
        UDPClientSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        UDPClientSocket.settimeout(0.5)

        # Send to server using created UDP socket
        try:
            try:
                UDPClientSocket.sendto(message.encode(), (ip, port))
                msgFromServer = UDPClientSocket.recvfrom(buffersize)
            except socket.timeout:
                return None
        except socket.gaierror:
            return None

        UDPClientSocket.close()

        return msgFromServer[0].decode()
