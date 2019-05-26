import socket
import threading
import struct
import cv2
import time
import os
import numpy

class webCamera:
    def __init__(self, resolution=(640,480), remoteAddress=("149.28.92.81", 9999)):
        self.resolution = resolution
        self.remoteAddress = remoteAddress
        self.img_quality = 15

    def setRemoteAddress(self, remoteAddress):
        self.remoteAddress = remoteAddress

    def setImageResolution(self, resolution):
        self.resolution = resolution

    def _setSocket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self._setSocket()
        self.socket.connect(self.remoteAddress)

    def recv__config(self):
        info = struct.unpack("lhh", self.socket.recv(12))
        if info[0] > 911:                   #print(info[0])
            self.img_quality = int(info[0])-911
            self.resolution = list(self.resolution)
            self.resolution[0] = info[1]
            self.resolution[1] = info[2]
            self.resolution = tuple(self.resolution)
            return 1
        else:
            return 0

    def _sendImage(self):
        if (self.recv__config() == 0):
            return
        camera = cv2.VideoCapture(0)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]
        while (1):
            (grabbed, self.img) = camera.read()
            self.img = cv2.resize(self.img, self.resolution)
            result, imgencode = cv2.imencode('.jpg', self.img, encode_param)
            img_code = numpy.array(imgencode)
            self.imgdata = img_code.tostring()
            try:
                self.socket.send(struct.pack("lhh", len(self.imgdata),
                                        self.resolution[0],
                                        self.resolution[1]) + self.imgdata)  # 长度，分辨率，图片内容

            except:
                camera.release()
                return

    def run(self):
            clientThread = threading.Thread(target = self._sendImage)
            clientThread.start()

def main():
    cam = webCamera()
    cam.connect()
    cam.run()

if __name__ == "__main__":
    main()

