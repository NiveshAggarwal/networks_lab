import socket
import select
import config

class IOHelper:
    def __init__(self):
        self.ack_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ack_socket.connect(('localhost', config.PORT_1))

        self.trial_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.trial_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.trial_server_socket.bind(('localhost', config.PORT_2))
        self.trial_server_socket.listen(1)
        self.trial_socket, _ = self.trial_server_socket.accept()

        self.output_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.output_socket.connect(('localhost', config.PORT_3))

        self.output_ack_socket_init = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.output_ack_socket_init.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.output_ack_socket_init.bind(('localhost', config.PORT_4))
        self.output_ack_socket_init.listen(1)
        self.output_ack_socket, _ = self.output_ack_socket_init.accept()

        self.noInput = -2
        self.terminated = -3
        self.isTerminated = False

        self.old_responses = []
    
    def consumeInput(self):
        if self.isTerminated:
            return (self.terminated, [])
        if len(self.old_responses) > 0:
            return self.old_responses.pop(0)
        readable, _, _ = select.select([self.trial_socket], [], [], 0.03)
        if readable:
            receiverId = self.trial_socket.recv(1024).decode()
            self.ack_socket.send(receiverId.encode())
            message = self.trial_socket.recv(1024).decode()
            if receiverId == '':
                self.ack_socket.close()
                self.trial_socket.close()
                self.trial_server_socket.close()
                self.isTerminated = True
                return (self.terminated, [])
            return (int(receiverId), [int(i) for i in message])
        else:
           return (self.noInput, [])

    def relayOutput(self, output):
        if type(output) == list:
            if type(output[0]) == int:
                output = ",".join([str(i) for i in output])
            else:
                output = ",".join([i for i in output])
        if type(output) == int:
            output = str(output)
        self.output_socket.send(output.encode())
        self.output_ack_socket.recv(1024)
        if output == "TERMINATED":
            self.output_ack_socket.close()
            self.output_ack_socket_init.close()
            self.output_socket.close()
            return -1
        return 0
    
    def insert(self, receiverId, message):
        self.old_responses = [(receiverId, message)] + self.old_responses

if __name__ == "__main__":
    from time import sleep
    IOHelperObj = IOHelper()
    while True:
        receiverId, message = IOHelperObj.consumeInput()
        if receiverId == IOHelperObj.terminated:
            break
        if receiverId == IOHelperObj.noInput:
            sleep(0.5)
        else:
            print(f"ReceiverId: {receiverId}, message: {message}")
    
    IOHelperObj.relayOutput(f"Acknowledgement :: ReceiverId: {receiverId}, message: {message}")