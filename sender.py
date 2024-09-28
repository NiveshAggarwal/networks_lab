import numpy as np
import pyaudio
import math
import config

class Sender:

    def __init__(self, base):
        self.base = base
        self.diff = config.F_DIFF
        self.frequencies = np.arange(config.F_LOW, config.F_LOW + self.diff * (self.base+1) , self.diff)

    def generate_waves(self, frequency: int, duration: float, sample_rate: int = 44100, amplitude: float=1) -> np.ndarray:
        '''
        Generate a sine waves of given frequency and duration.
        Parameters:
            frequency (int): Frequency of the tone in Hz
            duration (float): Duration of the tone in seconds
            sample_rate (int): Sampling rate in Hz (default: 44100)
            amplitude (float): Amplitude of the wave (0.0 to 1.0, default: 1)
        Returns:
            wave (np.ndarray): Numpy array containing the audio signal
        '''
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
        wave = amplitude * np.sin(2 * np.pi * frequency * t)
        return wave
    
    def convert_int_to_binary(self, num: int) -> list[int]:
        """
        Convert an integer to a list of bits.
        Parameters:
            num (int): Integer to convert
        Returns:
            binary (list[int]): List of bits
        """
        binary = []
        n = 5
        while n > 0:
            binary.append(num % 2)
            num = num // 2
            n -= 1
        return binary[::-1]
        
    def convert_list(self, message: list[int], base : int) -> np.ndarray:
        """
        Convert a list of bits to a list of integers.
        Parameters:
            message (list[int]): List of bits
            base (int): Base to convert the bits to
        Returns:
            converted_array (np.ndarray): Numpy array containing the converted integers
        """
        converted_array = np.array([])
        print(message)
        n=int(math.log2(base))
        if len(message)%n != 0:
            message = np.append(message, np.zeros(n - len(message)%n))
        for i in range(0, len(message), n):
            num = 0
            for j in range(0, n):
                num += message[i+j]*(2**(n-j-1))
            converted_array = np.append(converted_array, int(num)+1)

        return converted_array

    def change_base(self, message: list[int], base:int = 2) -> np.ndarray:
        """
        Convert a list of bits to a list of integers in a different base.
        Parameters:
            message (list[int]): List of bits
            base (int): Base to convert the bits to
        Returns:
            transmission (np.ndarray): Numpy array containing the converted integers
        """

        transmission=np.array([1,1,1,1,1,-1])                                           # special sequence
        # transmission = np.append(transmission, self.convert_list(message[0:5], base))   # preamble
        transmission = np.append(transmission, self.convert_list(self.convert_int_to_binary(len(message)), base))                     # append message length in 5 bits as premable     
        transmission = np.append(transmission, self.convert_list(message, base))    # tranmission message
        return transmission

    def encode_bits_to_audio(self, bits: np.ndarray, sample_rate: int = 44100, duration: float = 0.3, amplitude: float =1)-> np.ndarray:
        """
        Encode a list of bits into an audio signal.
        Parameters:
            bits (np.ndarray): List of bits (0s and 1s)
            sample_rate (int): Sampling rate in Hz
            duration (float): Duration of each signal in seconds
            amplitude (float): Amplitude of the wave
        Returns
            audio_signal (np.ndarray): Numpy array containing the audio signal
        """
        audio_signal = np.array([])
        
        transmission_msg_in_changed_base = self.change_base(bits, self.base)
        print(f"Sender.py:  Bits to be sent: {bits}")
        print(f"Sender.py:  Transmitted message in changed base: {transmission_msg_in_changed_base}")
        for i in transmission_msg_in_changed_base:
            audio_signal = np.append(audio_signal, self.generate_waves(self.frequencies[int(i)], duration/2, sample_rate, amplitude))
            audio_signal = np.append(audio_signal, self.generate_waves(self.frequencies[0], duration/2, sample_rate, amplitude))
        return audio_signal


    def send_audio(self, audio_signal: np.ndarray, sample_rate: int = 44100):
        """
        Send an audio signal to the default audio output device.
        Parameters:
            audio_signal (np.ndarray): Numpy array containing the audio signal
            sample_rate (int): Sampling rate in Hz
        """

        audio = pyaudio.PyAudio()
        
        stream = audio.open(format=pyaudio.paFloat32,
                            channels=1,
                            rate=sample_rate,
                            output=True)
        

        stream.write(audio_signal.astype(np.float32).tobytes())
        stream.stop_stream()
        stream.close()
        audio.terminate()