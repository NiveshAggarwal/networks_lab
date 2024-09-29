import socket
import time
import threading
import queue
import sys
import config

def printOutput():

    output_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    output_client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    output_client_socket.bind(('localhost', config.PORT_3))
    output_client_socket.listen(1)
    output_socket, _ = output_client_socket.accept()

    ack_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ack_socket.connect(('localhost', config.PORT_4))

    while True:
        data = output_socket.recv(1024)
        ack_socket.send(data)
        data = data.decode()
        if data == "TERMINATE":
            output_socket.close()
            ack_socket.close()
            output_client_socket.close()
            break
        if data:
            print(data)
            
if __name__ == "__main__":
    printOutput()