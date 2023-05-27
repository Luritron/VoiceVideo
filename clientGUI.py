import tkinter as tk
from tkinter import ttk
from PIL import ImageTk, Image
from math import sqrt, ceil

WIDTH=1280
HEIGHT=720


# 640x360 vid

GREY = '#666666'
GREY2 = '#555555'
BLACK = '#000000'
GREEN = '#50eda6'



class GUI:
    def __init__(self, root, clientNamesVideo={}, clientNamesAudio={}, currentFrames={}, clientSpeaking={}, toggleMuteIncoming=None, toggleMuteOutgoing=None, height=HEIGHT, width=WIDTH):
        self.clientNamesVideo = clientNamesVideo
        self.clientNamesAudio = clientNamesAudio
        self.currentFrames = currentFrames
        self.clientSpeaking = clientSpeaking
        self.toggleMuteIncoming = toggleMuteIncoming
        self.toggleMuteOutgoing = toggleMuteOutgoing
        self.root = root
        self.root.title('DoubleSpeak')

        basesizer = tk.Canvas(self.root, height=height, width=width, bd=0, relief='flat')
        basesizer.pack()

        gold = (1/1.618)
        self.canvas = tk.Canvas(self.root, bg=GREY, bd=2, relief='flat')
        self.canvas.place(relx=0, rely=0, relwidth=gold, relheight=1.0)

        self.frame = tk.Frame(self.root, bd=5, bg=GREY2, relief='groove')
        self.frame.place(relx=gold, rely=0, relwidth=1-gold, relheight=1.0)

        self.muteIncomingButton = tk.Button(
            self.frame,
            text="Mute Incoming",
            command=self.toggleMuteIncoming,
            highlightbackground=GREY2
        )
        self.muteIncomingButton.place(relx=0.25, rely=0.2, relwidth=0.5, relheight=0.25)

        self.muteOutgoingButton = tk.Button(
            self.frame,
            text="Mute Outgoing",
            command=self.toggleMuteOutgoing,
            highlightbackground=GREY2
        )
        self.muteOutgoingButton.place(relx=0.25, rely=0.6, relwidth=0.5, relheight=0.25)

        self.labels = []
        self.delay = int(1000/60)

        self.__lastHeight = self.canvas.winfo_height()
        self.__lastWidth = self.canvas.winfo_width()
        self.__photoImages = {}

        self.root.update()
        self.update()

        self.root.mainloop()

    def update(self):
        self.canvas.delete('all')

        #print('GUI Curr Frames: {}'.format(len(self.currentFrames)))

        newLabels = ((len(self.labels) != len(self.currentFrames)) or 
        (self.canvas.winfo_width() != self.__lastWidth) or
        (self.canvas.winfo_height() != self.__lastHeight))

        if newLabels:
            for lbl in self.labels:
                lbl.destroy()
            self.labels = [None for client in self.currentFrames]

        self.__lastHeight = self.canvas.winfo_height()
        self.__lastWidth = self.canvas.winfo_width()

        audioNameToNum = {v:k for k,v in self.clientNamesAudio.items()}

        for i, (clientNum, frame) in enumerate(sorted( self.currentFrames.items() )):
            x,y,w,h = self.getImageDimensions(i, len(self.currentFrames))
            
            #print(frame.shape)

            frameImg = Image.fromarray(frame).resize((w,h), Image.ANTIALIAS)
            photoImg = ImageTk.PhotoImage(image = frameImg)
            self.__photoImages[clientNum] = photoImg
            self.canvas.create_image(x,y, image=photoImg, anchor='nw', tag='vid')

            bd = 2

            if newLabels:
                self.labels[i] = tk.Label(self.canvas, text=self.clientNamesVideo.get(clientNum, '???'),fg='white', bg=GREY2)
                self.labels[i].place(x=x+5*bd, y=y+5*bd, anchor='nw')

            name = self.clientNamesVideo.get(clientNum, None)
            audioClientNum = None
            if name is not None:
                audioClientNum = audioNameToNum.get(name, None)
            ringColor = BLACK if not self.clientSpeaking.get(audioClientNum, False) else GREEN
            self.canvas.create_rectangle(x+bd//2,y+bd//2, x+w-bd//2, y+h-bd//2, width=bd, outline=ringColor, tag='rect')

        self.root.after(self.delay, self.update)

    def getImageDimensions(self, i, gridSize):
        ratio = 640/360
        bigW = self.canvas.winfo_width()
        bigH = self.canvas.winfo_height()

        ncols = int ( sqrt(gridSize) )
        nrows = ceil (gridSize / ncols)

        maxW = bigW // ncols
        maxH = bigH // nrows

        w = maxW
        h = maxH
        if w / ratio > h:
            w = int(ratio * h)
        else:
            h = int(w / ratio)

        x = (i % ncols) * w
        y = (i//ncols) * h
        return x,y,w,h

if __name__ == '__main__':
    root = tk.Tk()