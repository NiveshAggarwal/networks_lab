import random
from sender import *
import config
from time import *
from receiver_dll import *
from carrier_sense import *
from IOHelper import IOHelper
import math

if __name__ == "__main__":
    IOHelperObj = IOHelper()

def navSlots(messageLen=2):
    return math.ceil((messageLen+16+10)//int(np.log2(config.BASE)))+7+7+7+4

def createRTS(senderId,receiverId,messageLen):
    navT = navSlots(messageLen)
    message = list(f'{senderId:05b}')
    message += list(f'{receiverId:05b}')
    message += list(f'{navT:06b}')
    message = [int(i) for i in message]
    return message

def IdsFromCts(cts):
    # IOHelperObj.relayOutput(int(sum([(2**(4-i))*cts[i] for i in range(5)])))
    # IOHelperObj.relayOutput(int(sum([(2**(4-i))*cts[i+5] for i in range(5)])))
    return sum([(2**(4-i))*cts[i] for i in range(5)]), sum([(2**(4-i))*cts[i+5] for i in range(5)])

def checkACK(senderId ,receiverId ,ack) -> bool:
    senderIdGot, receiverIdGot = IdsFromCts(ack)
    return senderIdGot == senderId and receiverIdGot == receiverId

def send(receiverId:int, message: list[int]):
    receiver=Receiver(config.BASE)

    # #TODO: Should we carrier sense here?
    # while receiver.carrier_sense()[0] >= 0:            
    #     pass

    sender=Sender(config.BASE)
    encoded_audio=sender.encode_bits_to_audio(bits = createRTS(Id,receiverId,len(message)))

    print("RTS sent successfully. Waiting for CTS\n\n")

    sender.send_audio(encoded_audio)
    cts_length, cts = receiver.decode_audio_to_bits() 
    
    if cts_length == -1:
        return -1
    SenderIdGot,receiverIdGot = IdsFromCts(cts) 
    print("CTS received successfully. Sending message\n\n")
    if SenderIdGot != Id or receiverId != receiverIdGot:
        return -1                               # TODO: Receive CTS and wait for NAV
    encoded_message_audio=sender.encode_bits_to_audio(message)
    # sleep(config.SIFS)
    sender.send_audio(encoded_message_audio)

    IOHelperObj.relayOutput(f"[SENT]: {message} {receiverId} {time.time}")
    print("Message sent successfully. Waiting for ACK\n\n")

    ACK_length, ACK = receiver.decode_audio_to_bits()

    #TODO: Check if ACK is correct
    if ACK_length == -1:
        return -1
    if checkACK(Id, receiverId, ACK):
        return 0
    else:
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
        #TODO: Carrier sense for DIFS before sending
        if receiver.carrier_sense(total_duration=config.DIFS)[0] < 0:
            if backoffCounter <= 0:
                receiverId, message = IOHelperObj.consumeInput()
                # IOHelperObj.relayOutput(f"IDLE : {receiverId}, {message}")
                if receiverId == IOHelperObj.terminated:
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
                        IOHelperObj.insert(receiverId, message)     #TODO: Check where in the queue is it inserted
                        backoffCounterMax += 1 #TODO: need to change
                        backoffCounterMax=max(backoffCounterMax,backoffCounterCap)
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
            # IOHelperObj.relayOutput("BUSY")
            sender_id, message=receiver_dll(Id)
            if sender_id > 0:
                IOHelperObj.relayOutput(f"[RECVD] {message} {sender_id} {time.time}")
            #TODO: Print message properly