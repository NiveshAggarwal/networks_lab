import random
from sender import *
import config
from time import *
from receiver_dll import *
from carrier_sense import *
from IOHelper import IOHelper
import math
import ntplib

if __name__ == "__main__":
    IOHelperObj = IOHelper()

def navSlots(messageLen=2):
    return math.ceil((messageLen+16+10)//int(np.log2(config.BASE)))+7+7+7+4

def get_ntp_time(server='pool.ntp.org'):
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request(server)
        return ctime(response.tx_time)
    except ntplib.NTPException as e:
        print(f"NTP error: {e}")
        return -1
    except Exception as e:
        print(f"General error: {e}")
        return -1
        
def createRTS(senderId,receiverId,messageLen):
    navT = navSlots(messageLen)
    message = list(f'{senderId:05b}')
    message += list(f'{receiverId:05b}')
    message += list(f'{navT:06b}')
    message = [int(i) for i in message]
    return message

def decode(message: list[int], index: int = 0):
    if index==2:
        return int(''.join(map(str, message[index*5:index*5+6])), 2)
    else:
        return int(''.join(map(str, message[index*5:index*5+5])), 2)

def checkACK(senderId ,receiverId ,ack) -> bool:
    senderIdGot = decode(ack, 0)
    receiverIdGot = decode(ack, 1)
    return senderIdGot == senderId and receiverIdGot == receiverId

def send(receiverId:int, message: list[int]):
    receiver=Receiver(config.BASE)
    sender=Sender(config.BASE)

    encoded_audio=sender.encode_bits_to_audio(bits = createRTS(Id,receiverId,len(message)))
    sender.send_audio(encoded_audio)
    print("RTS sent successfully. Waiting for CTS\n\n")

    cts_length, cts = receiver.decode_audio_to_bits() 
    if cts_length == -1:
        print("CTS not received within timeout time\n\n")
        return -1

    receiverIdGot = decode(cts, 1)
    senderIdGot = decode(cts, 0) 
    if senderIdGot != Id or receiverId != receiverIdGot:
        print("CTS has incorrect sender or receiver ID\n\n")
        sleep(decode(cts, 2)*config.BIT_DURATION)
        return -1                               # TODO: Receive CTS and wait for NAV
    print("CTS received successfully. Sending message\n\n")

    encoded_message_audio=sender.encode_bits_to_audio(message)
    sender.send_audio(encoded_message_audio)
    IOHelperObj.relayOutput(f"[SENT]: {message} {receiverId} {get_ntp_time()}")
    print("Message sent successfully. Waiting for ACK\n\n")

    ACK_length, ACK = receiver.decode_audio_to_bits()
    if ACK_length == -1:
        print("ACK not received within timeout time\n\n")
        return -1
    if checkACK(Id, receiverId, ACK):
        return 0
    else:
        print("ACK has incorrect sender or receiver ID\n\n")
        return -1
    


if __name__ == "__main__":

    Id=int(input("Enter the ID of this device : "))
    backoffCounter = 0
    backoffCounterMax = 1
    collisions=0
    maxCollsions=15
    backoffCounterCap = 3       # Can be scaled it as per requirements
    receiver=Receiver(config.BASE)
    while True:
        if receiver.carrier_sense(total_duration=config.DIFS)[0] < 0:
            if backoffCounter <= 0:
                receiverId, message = IOHelperObj.consumeInput()
                if receiverId == -1:
                    continue
                elif receiverId == IOHelperObj.terminated:
                    break
                elif receiverId != IOHelperObj.noInput:
                    print(f"ReceiverId: {receiverId}, message: {message}")
                    if send(receiverId, message) != 0:
                        collisions+=1
                        if collisions > maxCollsions:
                            backoffCounter = 0
                            backoffCounterMax = 1
                            collisions = 0
                            continue
                        IOHelperObj.insert(receiverId, message)
                        backoffCounterMax += 1
                        backoffCounterMax=min(backoffCounterMax,backoffCounterCap)
                        backoffCounter = random.randint(0, 2**backoffCounterMax)
                    else:
                        print("Message sent successfully. ACK received\n\n")
                        sleep(1)
                        collisions = 0
                        backoffCounter = 0
                        backoffCounterMax = 1
            else:

                backoffCounter -= 1
        else:
            sender_id, message=receiver_dll(Id)
            if sender_id > 0:
                IOHelperObj.relayOutput(f"[RECVD]: {message} {sender_id} {get_ntp_time()}")