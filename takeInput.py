import socket
import time
import sys
import queue
import threading
import config

messageQueue = queue.Queue()

def post_inputs():
    
    ack_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ack_client_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    ack_client_socket.bind(('localhost', config.PORT_1))
    ack_client_socket.listen(1)

    ack_socket, _ = ack_client_socket.accept()
    
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', config.PORT_2))

    while True:
        if messageQueue.qsize() > 0:
            receiverId, message = messageQueue.get()
            messageQueue.task_done()
            client_socket.send(receiverId.encode())
            data = ack_socket.recv(1024).decode()
            client_socket.send(message.encode())


def get_input():

    num_inputs = int(input("Enter number of messages to be sent : "))

    input_array = []

    for i in range(num_inputs):
        receiverId_message = input('Enter first line of input : ')
        message = receiverId_message.split(' ')[0]
        receiverId = receiverId_message.split(' ')[1]
        input_array.append((receiverId, message))


    for i in range(num_inputs):
        receiverId, message = input_array.pop(0)
        input("Press enter to trigger message transmission")
        if int(receiverId) != -1:
            messageQueue.put((receiverId, message))

if __name__ == "__main__":

    thread_1 = threading.Thread(target=post_inputs)
    thread_2 = threading.Thread(target=get_input)
 
    thread_1.start()
    thread_2.start()

    thread_1.join()
    thread_2.join()