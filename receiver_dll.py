from carrier_sense import *
from crc import *
from sender import *
from time import sleep
import config
from lab3main import checkACK
import math


def decode(message: list[int], index: int = 0):
    if index==2:
        return int(''.join(map(str, message[index*5:index*5+10])), 2)
    else:
        return int(''.join(map(str, message[index*5:index*5+5])), 2)

def cts(sender_id,reciever_id,nav):
    message = list(f'{sender_id:05b}')
    message += list(f'{reciever_id:05b}')
    message += list(f'{nav:010b}')
    message = [int(i) for i in message]
    return message

def acknowledge(sender_id,reciever_id):
    message = list(f'{sender_id:05b}')
    message += list(f'{reciever_id:05b}')
    message = [int(i) for i in message]
    return message


def receiver_dll_broadcast(id:int, sender_id:int, receiver : Receiver, sender : Sender):

    message_length, message = receiver.decode_audio_to_bits(timeout = config.TIMEOUT+config.SIFS)
    if message_length < 0:
        print("Message not received within timeout time")
        return -1, []
    
    message = [int(i) for i in message]
    print("Message received successfully. Sending ACK\n\n")

    ackId = 1
    while ackId <= 3:
        if ackId == sender_id :
            ackId += 1
            continue
        if ackId == id:
            sleep(config.SIFS)
            audio_signal = sender.encode_bits_to_audio(acknowledge(sender_id,id))
            sender.send_audio(audio_signal)
            print(f"ACK {acknowledge(sender_id,id)} sent successfully\n\n")
            ackId += 1
            return sender_id, message
        else:
            ACK_length, ACK = receiver.decode_audio_to_bits(timeout = config.TIMEOUT+config.SIFS)
            if ACK_length < 10:
                print(f"ACK of {ackId} not received within timeout time\n\n")
                return -1, []
            if checkACK(sender_id, ackId, ACK):
                ackId += 1
            else:
                print("ACK has incorrect sender or receiver ID\n\n")
                return -1, []
    
    return -1, []


def receiver_dll(noise_power:np.ndarray, id:int):
    receiver = Receiver(config.BASE)
    sender = Sender(config.BASE)
    receiver.noise = noise_power
    rts_length, rts = receiver.decode_audio_to_bits()
    if rts_length < 15:
        print("RTS not received within timeout time\n\n")
        return -1, []
    nav=decode(rts, 2)
    sender_id = decode(rts, 0)

    if decode(rts, 1) == 0:
        return receiver_dll_broadcast(id, sender_id, receiver, sender)
    
    if(decode(rts,1)!=id):
        print(f"RTS from {sender_id} not meant for me\n\n")
        if(decode(rts,0)>3  or decode(rts,0)<1 or decode(rts,1)>3):
            return -1, [] 
        sleep(min(nav*config.BIT_DURATION,(2*6+math.ceil((15+config.ACK +3*5+3*config.CRC)/config.LOG_BASE))*config.BIT_DURATION+2*config.SIFS))  
        return -1, []

    print("RTS received successfully. Sending CTS\n\n")
    sleep(config.SIFS)
    print(f"NAV: {nav}")
    print(nav-(6+(math.ceil((config.CTS+5+config.CRC)/config.LOG_BASE))))
    audio_signal = sender.encode_bits_to_audio(cts(sender_id,id,max(0,nav-(6+(math.ceil((config.CTS+5+config.CRC)/config.LOG_BASE))))))
    sender.send_audio(audio_signal)
    print(f"CTS {cts(sender_id,id,nav-(6+(math.ceil((config.CTS+5+config.CRC)/config.LOG_BASE))))} sent successfully. Waiting for message\n\n")    

    message_length, message = receiver.decode_audio_to_bits(timeout = config.TIMEOUT+config.SIFS)
    if message_length < 0:
        print("Message not received within timeout time")
        return -1, []
    
    message = [int(i) for i in message]
    sleep(config.SIFS)
    print("Message received successfully. Sending ACK\n\n")
    
    audio_signal = sender.encode_bits_to_audio(acknowledge(sender_id,id))
    sender.send_audio(audio_signal)
    print(f"ACK {acknowledge(sender_id,id)} sent successfully\n\n")

    return sender_id, message


    