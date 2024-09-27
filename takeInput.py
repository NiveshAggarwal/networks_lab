import socket
import time
import threading
import queue
import sys
import config

messageQueue = queue.Queue(maxsize=1024)


def takeInput():
    while True:
        sys.stdout.write("\rEnter the receiverId please: ")
        receiverId : int = input()
        message = input("Enter the message please: ")
        messageQueue.put((receiverId, message))


def send_input():
    ack_client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ack_client_socket.bind(('localhost', config.PORT_1))
    ack_client_socket.listen(1)

    ack_socket, _ = ack_client_socket.accept()
    time.sleep(2)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(('localhost', config.PORT_2))

    while True:
        if messageQueue.qsize() > 0:
            receiverId, message = messageQueue.get(block = False)
            messageQueue.task_done()

            client_socket.send(receiverId.encode())
            data = ack_socket.recv(1024).decode()
            client_socket.send(message.encode())
            # data = ack_socket.recv(1024).decode()

            if int(receiverId) < 0:
                client_socket.close()
                ack_socket.close()
                ack_client_socket.close()
                break
        else:
            time.sleep(0.5)


if __name__ == "__main__":
    thread_1 = threading.Thread(target=takeInput)
    thread_2 = threading.Thread(target=send_input)
    # thread_3 = threading.Thread(target=printOutput)

    thread_1.start()
    thread_2.start()
    # thread_3.start()

    thread_1.join()
    thread_2.join()
    # thread_3.join()