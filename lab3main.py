import random
from sender import *
import config
from time import *
from receiver_dll import *
from carrier_sense import *
from IOHelper import IOHelper
import math
import ntplib
from datetime import datetime

def navSlots(messageLen=2):
    return math.ceil((messageLen+config.CTS+config.ACK+3*config.CRC)/config.LOG_BASE)+math.ceil(3*(6+5/config.LOG_BASE))

def get_ntp_time(server='time.google.com'):
    try:
        ntp_client = ntplib.NTPClient()
        response = ntp_client.request(server)
        return response.tx_time
    except ntplib.NTPException as e:
        return -1
    except Exception as e:
        return -1
    
def print_time(syncTime, syncBase):
    return ctime(syncTime + time() - syncBase)

def createRTS(senderId,receiverId,messageLen):
    navT = navSlots(messageLen)
    message = list(f'{senderId:05b}')
    message += list(f'{receiverId:05b}')
    message += list(f'{navT:010b}')
    message = [int(i) for i in message]
    return message

def decode(message: list[int], index: int = 0):
    if index==2:
        return int(''.join(map(str, message[index*5:index*5+10])), 2)
    else:
        return int(''.join(map(str, message[index*5:index*5+5])), 2)

def checkACK(senderId ,receiverId ,ack) -> bool:
    senderIdGot = decode(ack, 0)
    receiverIdGot = decode(ack, 1)
    return senderIdGot == senderId and receiverIdGot == receiverId

def send(noise_power:np.ndarray, receiverId:int, message: list[int]):
    receiver=Receiver(config.BASE)
    sender=Sender(config.BASE)
    receiver.noise = noise_power
    encoded_audio=sender.encode_bits_to_audio(bits = createRTS(Id,receiverId,len(message)))
    sender.send_audio(encoded_audio)
    print(f"RTS {createRTS(Id,receiverId,len(message))} sent successfully. Waiting for CTS\n\n")

    cts_length, cts = receiver.decode_audio_to_bits(timeout = config.TIMEOUT+config.SIFS) 
    if cts_length < 15:
        print("CTS not received within timeout time\n\n")
        return -1

    receiverIdGot = decode(cts, 1)
    senderIdGot = decode(cts, 0) 
    if senderIdGot != Id or receiverId != receiverIdGot:
        print("CTS has incorrect sender or receiver ID\n\n")
        if(receiverId>3 or senderIdGot>3 or receiverIdGot==0 or senderIdGot==0):
            return -1
        sleep(min(decode(cts, 2)*config.BIT_DURATION,(2*6+math.ceil((15+config.ACK +2*5+2*config.CRC)/config.LOG_BASE))*config.BIT_DURATION+config.SIFS))  
        return -1 
    print("CTS received successfully. Sending message\n\n")

    sleep(config.SIFS)
    encoded_message_audio=sender.encode_bits_to_audio(message)
    sender.send_audio(encoded_message_audio)
    print(f"Message {message} sent successfully. Waiting for ACK\n\n")

    ACK_length, ACK = receiver.decode_audio_to_bits(timeout = config.TIMEOUT+config.SIFS)
    if ACK_length == -1:
        print("ACK not received within timeout time\n\n")
        return -1
    if checkACK(Id, receiverId, ACK):
        IOHelperObj.relayOutput(f"[SENT]: {message} {receiverId} {print_time(syncTime,syncBase)}")
        return 0
    else:
        print("ACK has incorrect sender or receiver ID\n\n")
        return -1
    
def send_broadcast(noise_power:np.ndarray, receiverId:int, message: list[int]):
    receiver=Receiver(config.BASE)
    sender=Sender(config.BASE)
    receiver.noise = noise_power
    encoded_audio=sender.encode_bits_to_audio(bits = createRTS(Id,receiverId,len(message)))
    sender.send_audio(encoded_audio)
    print(f"RTS_BROADCAST {createRTS(Id,receiverId,len(message))} sent successfully. Now sending message ....\n\n")


    sleep(config.SIFS)
    encoded_message_audio=sender.encode_bits_to_audio(message)
    sender.send_audio(encoded_message_audio)
    print(f"Message {message} sent successfully. Waiting for ACKs\n\n")


    ackId = 1

    while ackId <= 3:
        if ackId == Id :
            ackId += 1
            continue
        ACK_length, ACK = receiver.decode_audio_to_bits(timeout = config.TIMEOUT+config.SIFS)
        if ACK_length < 10:
            print(f"ACK of {ackId} not received within timeout time\n\n")
            return -1
        if checkACK(Id, ackId, ACK):
            IOHelperObj.relayOutput(f"[SENT]: {message} {ackId} {print_time(syncTime,syncBase)}")
        else:
            print("ACK has incorrect sender or receiver ID\n\n")
            return -1
        ackId += 1
    
    return 0


if __name__ == "__main__":
    IOHelperObj = IOHelper()
    while True:
        syncTime = get_ntp_time()
        syncBase= time()
        if syncTime > 0:
            break

    Id=int(input("Enter the ID of this device : "))
    backoffCounter = 0
    backoffCounterMax = 1
    collisions=0
    maxCollsions=15
    backoffCounterCap = 3       # Can be scaled it as per requirements
    receiver=Receiver(config.BASE)
    receiver.calibrate()

    while True:
        if receiver.carrier_sense(total_duration=config.DIFS)[0] < 0:
            if backoffCounter <= 0:
                receiverId, message = IOHelperObj.consumeInput()
                if receiverId == -1:
                    continue
                elif receiverId == IOHelperObj.terminated:
                    continue
                elif receiverId != IOHelperObj.noInput:
                    print(f"ReceiverId: {receiverId}, message: {message}")
                    if receiverId == 0:
                        if send_broadcast(receiver.noise, receiverId, message) != 0:
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
                            print("Broadcast sent successfully. ACKs received\n\n")
                            # sleep(1)
                            collisions = 0
                            backoffCounter = 0
                            backoffCounterMax = 1
                    else:
                        if send(receiver.noise, receiverId, message) != 0:
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
                            # sleep(1)
                            collisions = 0
                            backoffCounter = 0
                            backoffCounterMax = 1
            else:
                while receiver.carrier_sense(total_duration=config.SLOT_DURATION)[0] < 0 and backoffCounter > 0:
                    backoffCounter -= 1     
                
                if backoffCounter <= 0:
                    receiverId, message = IOHelperObj.consumeInput()
                    if receiverId == -1:
                        continue
                    elif receiverId == IOHelperObj.terminated:
                        continue
                    elif receiverId != IOHelperObj.noInput:
                        print(f"ReceiverId: {receiverId}, message: {message}")
                        if receiverId == 0:
                            if send_broadcast(receiver.noise, receiverId, message) != 0:
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
                                print("Broadcast sent successfully. ACKs received\n\n")
                                # sleep(1)
                                collisions = 0
                                backoffCounter = 0
                                backoffCounterMax = 1

                        else:
                            if send(receiver.noise, receiverId, message) != 0:
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
                                # sleep(1)
                                collisions = 0
                                backoffCounter = 0
                                backoffCounterMax = 1

                else:
                    sender_id, message=receiver_dll(receiver.noise, Id)
                    if sender_id > 0:
                        IOHelperObj.relayOutput(f"[RECVD]: {message} {sender_id} {get_ntp_time()}") 
        else:
            sender_id, message=receiver_dll(receiver.noise, Id)
            if sender_id > 0:
                IOHelperObj.relayOutput(f"[RECVD]: {message} {sender_id} {print_time(syncTime,syncBase)}")