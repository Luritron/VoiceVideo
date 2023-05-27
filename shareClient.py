import videoClient
import audioClient
import clientGUI
import netpack
import tkinter as tk

class MediaClient():
    def __init__(self, name):
        self.name = name
        self.__clientNamesVideo = {videoClient.ME:name}
        self.__clientNamesAudio = {audioClient.ME:name}
        self.__currentFrames = {}
        self.__clientSpeaking = {}

        self.audio = None
        self.video = None

        self.__root = tk.Tk()

    def setAudioServer(self, audioHost, audioPort):
        self.audio = audioClient.AudioClient(audioHost, audioPort, name=name)
        self.__clientNamesAudio = self.audio.clientNames

    def setVideoServer(self, videoHost, videoPort):
        self.video = videoClient.VideoClient(videoHost, videoPort, name=name)
        self.__clientNamesVideo = self.video.clientNames
        
    def startAudio(self):
        ret = self.audio.start()
        self.__clientSpeaking = self.audio.isSpeaking
        return ret

    def startVideo(self):
        ret = self.video.start()
        self.__currentFrames = self.video.currentFrames
        return ret
    
    def toggleMuteIncoming(self):
        if self.audio:
            self.audio.toggleMuteIncoming()

    def toggleMuteOutgoing(self):
        if self.audio:
            self.audio.toggleMuteOutgoing()

    def startGui(self):
        self.GUI = clientGUI.GUI(
            self.__root,
            clientNamesVideo=self.__clientNamesVideo,
            clientNamesAudio=self.__clientNamesAudio,
            currentFrames=self.__currentFrames,
            clientSpeaking=self.__clientSpeaking,
            toggleMuteIncoming=self.toggleMuteIncoming,
            toggleMuteOutgoing=self.toggleMuteOutgoing
        )

    def startAll(self):
        self.startAudio()
        self.startVideo()
        self.startGui()

if __name__ == "__main__":
    name = input("Enter name\n")
    client = MediaClient(name=name)

    # External server AWS EC2
    client.setAudioServer('52.59.203.3', 8000)
    client.setVideoServer('52.59.203.3', 8100)
    
    # Local server 127.0.0.1
    # client.setAudioServer('127.0.0.1', 8000)
    # client.setVideoServer('127.0.0.1', 8100)
    
    while not client.audio.connected:
        client.startAudio()

    while not client.video.connected:
        client.startVideo()

    client.startGui()
