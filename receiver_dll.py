from carrier_sense import *
from crc import *
from sender import *
from time import sleep
import config

sifs = 0.6

def decode(message: list[int], index: int = 0):
    return int(''.join(map(str, message[index*5:index*5+5])), 2)

def cts(sender_id,reciever_id,nav):
    message += list(f'{sender_id:05b}')
    message += list(f'{reciever_id:05b}')
    message += list(f'{nav:05b}')
    return message

def acknowledge(sender_id,reciever_id):
    message = list(f'{sender_id:05b}')
    message += list(f'{reciever_id:05b}')
    return message

def receiver_dll(id:int, noise_power: np.ndarray):

    receiver = Receiver(config.BASE)
    receiver.noise = noise_power
    sender = Sender(config.BASE)
    rts_length, rts = receiver.decode_audio_to_bits()
    print(rts)
    if rts_length < 15:
        return -1
    nav=decode(rts, 2)
    if(decode(message,1)!=id):
        # nav = decode(rts, 2)
        nav = config.NAVTIME  
        sleep(nav)  #TODO Use NAV function
        return -1
    sender_id = decode(rts, 0)
    sleep(sifs)
    audio_signal = sender.encode_bits_to_audio(cts(sender_id,id,nav))
    sender.send_audio(audio_signal)
    
    #TODO: Max time is SIFS or timeout. Change maxtime to "timeout"
    _, message = receiver.decode_audio_to_bits()

    sleep(sifs)
    audio_signal = sender.encode_bits_to_audio(acknowledge(sender_id,id))
    sender.send_audio(audio_signal)

    return message


    
