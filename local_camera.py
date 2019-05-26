import socket
import threading
import struct
import cv2
import time
import os
import numpy
# 问题处在发送端 发送过程中有丢帧

class webCamera:
    def __init__(self, resolution = (640, 480), host = ("", 7999)):
        self.resolution = resolution
        self.host = host
        self.setSocket(self.host)
        self.img_quality = 15

    def setImageResolution(self, resolution):
        self.resolution = resolution

    def setHost(self, host):
        self.host = host

    def setSocket(self, host):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.host)
        self.socket.listen(5)
        print("Server running on port:%d" % host[1])

    def recv__config(self, client):
        info = struct.unpack("lhh", client.recv(12))
        if info[0] > 911:                   #print(info[0])
            self.img_quality = int(info[0])-911
            self.resolution = list(self.resolution)
            self.resolution[0] = info[1]
            self.resolution[1] = info[2]
            self.resolution = tuple(self.resolution)
            return 1
        else:
            return 0

    def _processConnection(self, client, addr):
        if(self.recv__config(client) == 0):
            return
        camera = cv2.VideoCapture(0)
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), self.img_quality]
        f = open("video_info.txt", 'a+')
        print("Got connection from %s:%d" % (addr[0], addr[1]), file=f)
        print("Resolution:%d * %d" % (self.resolution[0], self.resolution[1]), file=f)
        print("Camera open successfully!", file=f)
        print("Start connection time:%s" % time.strftime("%Y-%m-%d %H:%M:%S",
                                              time.localtime(time.time())), file=f)
        # print(camera.get(5), file=f)
        f.close()

        while(1):
            (grabbed, self.img) = camera.read()
            self.img = cv2.resize(self.img, self.resolution)
            result, imgencode = cv2.imencode('.jpg', self.img, encode_param)
            img_code = numpy.array(imgencode)
            self.imgdata = img_code.tostring()
            try:
                client.send(struct.pack("lhh", len(self.imgdata),
                                        self.resolution[0],
                                        self.resolution[1])+self.imgdata)   # 长度，分辨率，图片内容

            except:
                f = open("video_info.txt", 'a+')
                print("%s:%d disconnected!" % (addr[0], addr[1]), file=f)
                print("Over connection time:%s" % time.strftime("%Y-%m-%d %H:%M:%S",
                                                      time.localtime(time.time())), file=f)
                print("*****************************************************", file=f)
                camera.release()
                f.close()
                return

    def run(self):
        while(1):
            print("waiting...")
            client, addr = self.socket.accept()
            clientThread = threading.Thread(target = self._processConnection, args=(client, addr, ))
            clientThread.start()

def main():
    cam = webCamera()
    cam.run()

if __name__ == "__main__":
    main()


