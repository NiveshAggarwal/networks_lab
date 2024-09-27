# import queue
import random
# import threading
from sender import *
import config
from time import sleep
from receiver_dll import *
from carrier_sense import *
from IOHelper import IOHelper

if __name__ == "__main__":
    IOHelperObj = IOHelper()

def navTime(messageLen=2):
    return config.NAVTIME

def createRTS(senderId,receiverId,messageLen):
    navT = navTime(messageLen)
    IOHelperObj.relayOutput([((senderId>>i) & 1) for i in range(5)] + [((receiverId>>i) & 1) for i in range(5)] + [((navT>>i) & 1) for i in range(5)])
    return [((senderId>>i) & 1) for i in range(5)] + [((receiverId>>i) & 1) for i in range(5)] + [((navT>>i) & 1) for i in range(5)]

def IdsFromCts(cts):
    IOHelperObj.relayOutput(sum([(2**(4-i))*cts[i] for i in range(5)]))
    IOHelperObj.relayOutput(sum([(2**(4-i))*cts[i+5] for i in range(5)]))
    return sum([(2**(4-i))*cts[i] for i in range(5)]), sum([(2**(4-i))*cts[i+5] for i in range(5)])

def checkACK(senderId ,receiverId ,ack) -> bool:
    senderIdGot, receiverIdGot = IdsFromCts(ack)
    return senderIdGot == senderId and receiverIdGot == receiverId

def send(receiverId,message):
    receiver=Receiver(config.BASE)

    #TODO: Should we carrier sense here?
    while receiver.carrier_sense()[0] >= 0:            
        pass

    sender=Sender(config.BASE)
    encoded_audio=sender.encode_bits_to_audio(bits = createRTS(Id,receiverId,len(message)))
    sleep(config.SIFS) #TODO: Don't sleep here. 
    sender.send_audio(encoded_audio)
    cts_length, cts = receiver.decode_audio_to_bits(max_time=config.SIFS)  #TODO: max_time is SIFS or timeout. Change maxtime to "timeout"
    # cts=decodeCrc(transmission=tranmission, bits=bits)
    if cts_length == -1:
        return -1
    SenderIdGot,receiverIdGot = IdsFromCts(cts) #TODO: Check if this is correct
    if SenderIdGot != Id or receiverId != receiverIdGot:
        return -1                               # TODO: Receive CTS and wait for NAV
    encoded_message_audio=sender.encode_bits_to_audio(message)
    sleep(config.SIFS)
    sender.send_audio(encoded_message_audio)
    ACK_length, ACK = receiver.decode_audio_to_bits(max_time=config.SIFS)
    # ACK=decodeCrc(transmission=ack_Tranmission, bits=ack_Bits)

    #TODO: Check if ACK is correct
    if ACK_length == -1:
        return -1
    if checkACK(receiverId, receiverId, ACK):
        return -1
    else:
        return 0
    


if __name__ == "__main__":
    Id=int(input("Enter the ID of this device : "))
    # input_thread = threading.Thread(target=takeInput)
    # input_thread.start()

    # IOHelperObj = IOHelper()
    
    backoffCounter = 0
    backoffCounterMax = 2
    receiver=Receiver(16)
    while True:
        #TODO: Carrier sense for DIFS before sending
        if receiver.carrier_sense()[0] < 0:
            if backoffCounter <= 0:
                receiverId, message = IOHelperObj.consumeInput()
                # IOHelperObj.relayOutput(f"IDLE : {receiverId}, {message}")
                if receiverId == IOHelperObj.terminated:
                    break
                elif receiverId != IOHelperObj.noInput:
                    if send(receiverId, message) != 0:
                        IOHelperObj.insert(receiverId, message)     #TODO: Check where in the queue is it inserted
                        backoffCounterMax *= 2 #TODO: need to change
                        backoffCounter = random.randint(0, backoffCounterMax)
            else:
                backoffCounter -= 1
        else:
            IOHelperObj.relayOutput("BUSY")
            message=receiver_dll(id)
            #TODO: Print message properly
        sleep(0.03)