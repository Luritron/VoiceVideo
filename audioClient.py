from socket import socket, AF_INET, SOCK_DGRAM, timeout
from threading import Thread
import pyaudio
from array import array
from netpack import Netpack, PackType
from time import time

OK = 'ok'
PINGME = 'pingme'
DEFAULT_BUFFER_SIZE = 2049
CLIENT_CONNECTION_TIMEOUT = 7.5
START_PINGING = 4.5
ME = -1

def getDefaultAudioSettings():
    DEFAULT_AUDIO_SETTINGS = {
        'FORMAT':pyaudio.paInt16, 
        'CHANNELS':1, 
        'RATE':44100, 
        'CHUNK':1024, 
        'THRESHOLD':500}
    return DEFAULT_AUDIO_SETTINGS

class AudioClient:
    def __init__(self, serverHost, serverPort, bufferSize=DEFAULT_BUFFER_SIZE, 
    audioSettings=getDefaultAudioSettings(), name='client'):

        self.server = (serverHost, serverPort)
        self.client = socket(family=AF_INET, type=SOCK_DGRAM)
        #self.client.settimeout(CLIENT_CONNECTION_TIMEOUT)
        self.bufferSize = bufferSize

        self.muteIncoming = False
        self.muteOutgoing = False

        self.audio=pyaudio.PyAudio()
        self.streamIn = self.audio.open(
            format=audioSettings['FORMAT'],
            channels=audioSettings['CHANNELS'], 
            rate=audioSettings['RATE'], 
            frames_per_buffer=audioSettings['CHUNK'],
            input=True, output=False)

        self.streamsOut = {}
        self.isSpeaking = {}
        self.clientNames = {ME:name}
        
        self.sendThread = None
        self.receiveThread = None
        self.name = name
        self.audioSettings = audioSettings
        self.lastReceived = time()
        self.connected = False

    def addOutputStream(self, char):
        audioSettings = self.audioSettings
        self.streamsOut[char] = self.audio.open(
            format=audioSettings['FORMAT'],
            channels=audioSettings['CHANNELS'], 
            rate=audioSettings['RATE'], 
            frames_per_buffer=audioSettings['CHUNK'],
            input=False, output=True)

    def connectToServer(self):
        if self.connected:
            return True

        datapack = Netpack(packType=PackType.Handshake, data=self.name.encode(encoding='UTF-8'))
        self.client.sendto(datapack.out(), self.server)

        data, addr = self.client.recvfrom(self.bufferSize)
        datapack = Netpack(datapacket=data)

        if (addr==self.server and datapack.PackType==PackType.Handshake and 
        datapack.data.decode('UTF-8')==OK):
            print('Connected to server successfully!')
            self.connected = True
        return self.connected

    def start(self):
        self.connectToServer()
        if self.connected:
            self.receiveThread = Thread(target=self.recieveAudio)
            self.receiveThread.start()

            self.sendThread = Thread(target=self.sendAudio)
            self.sendThread.start()
        return self.connected
    
    def toggleMuteIncoming(self):
        self.muteIncoming = not self.muteIncoming

    def toggleMuteOutgoing(self):
        self.muteOutgoing = not self.muteOutgoing

    def sendAudio(self):
        while self.connected:
            if time() - self.lastReceived >= START_PINGING:
                pingpack = Netpack(packType=PackType.KeepAlive, data=PINGME.encode('UTF-8'))
                self.client.sendto(pingpack.out(), self.server)

            if not self.muteOutgoing:
                data = self.streamIn.read(self.audioSettings['CHUNK'], exception_on_overflow=False)
                vol = max(array('h', data))
                if vol > self.audioSettings['THRESHOLD']:
                    datapack = Netpack(packType=PackType.ClientData, data=data)
                    self.client.setblocking(False)
                    try:
                        self.client.sendto(datapack.out(), self.server)
                    except BlockingIOError:
                        pass
                    finally:
                        self.client.setblocking(True)
                    self.isSpeaking[ME] = True
                else:
                    self.isSpeaking[ME] = False
            else:
                self.isSpeaking[ME] = False

    def sendAudio(self):
        while self.connected:
            if time() - self.lastReceived >= START_PINGING:
                pingpack = Netpack(packType=PackType.KeepAlive, data=PINGME.encode('UTF-8'))
                self.client.sendto(pingpack.out(), self.server)

            if not self.muteOutgoing:
                data = self.streamIn.read(self.audioSettings['CHUNK'], exception_on_overflow=False)
                vol = max(array('h', data))
                if vol > self.audioSettings['THRESHOLD']:
                    datapack = Netpack(packType=PackType.ClientData, data=data)
                    self.client.setblocking(False)
                    try:
                        self.client.sendto(datapack.out(), self.server)
                    except BlockingIOError:
                        pass
                    finally:
                        self.client.setblocking(True)
                    self.isSpeaking[ME] = True
                else:
                    self.isSpeaking[ME] = False
            else:
                self.isSpeaking[ME] = False
 
    def recieveAudio(self):
        while self.connected:
            try:
                data, addr = self.client.recvfrom(self.bufferSize)
                datapack = Netpack(datapacket=data)
                self.lastReceived = time()
                self.updateIsSpeaking()

                if not self.muteIncoming:
                    if datapack.PackType == PackType.ClientData:
                        char = datapack.head
                        if self.streamsOut.get(char, None) is None:
                            self.addOutputStream(char)
                            self.queryForName(char)
                
                        self.streamsOut[char].write(datapack.data)

                        if self.clientNames.get(char, None) is None:
                            self.queryForName(char)

                elif datapack.PackType == PackType.KeepAlive and datapack.data.decode() == PINGME:
                    outpack = Netpack(packType=PackType.KeepAlive, data=OK.encode('UTF-8'))
                    self.client.sendto(outpack.out(), self.server)

                elif datapack.PackType == PackType.NameQuery:
                    query = datapack.data.decode(encoding='UTF-8')
                    char = int(query.split(':')[0])
                    name = query.split(':')[1]
                    self.clientNames[char] = name

            except BlockingIOError:
                pass
            except timeout:
                self.connected = False
                print('Lost connection to server!')

    def queryForName(self, clientNum):
        outpack = Netpack(packType=PackType.NameQuery, data=str(clientNum).encode(encoding='UTF-8'))
        self.client.sendto(outpack.out(), self.server)

    def updateIsSpeaking(self):
        for char, stream in self.streamsOut.items():
            self.isSpeaking[char] = (stream.get_write_available() < self.audioSettings['CHUNK']*4)

if __name__ == "__main__":
    name = input("Enter name\n")

    client = AudioClient('127.0.0.1', 8000, name=name)
    client.start()

    client.receiveThread.join()
    client.sendThread.join()
    