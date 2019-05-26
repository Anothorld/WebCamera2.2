#!/usr/local/bin/python3.6
#-*-coding:utf-8 -*-

import socket
import threading
import struct
import os
import time
import sys
import numpy
import cv2
import re
from queue import Queue

class webCamConnect:
    def __init__(self, resolution = [640, 480], cameraAddress = ("", 9999),
                 windowName = "video"):
        self.cameraAddress = cameraAddress
        self.setSocket(self.cameraAddress)
        self.resolution = resolution
        self.name = windowName
        self.mutex = threading.Lock()
        self.src = 911 + 15
        self.interval = 0
        self.back_up = 0
        self.path = os.getcwd()
        self.img_quality = 15
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.stopflag = 0

    def setHost(self, cameraAddress):
        self.cameraAddress = cameraAddress

    def setImageResolution(self, resolution):
        self.resolution = resolution

    def setSocket(self, cameraAddress):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.cameraAddress)
        self.socket.listen(5)
        print("Listening port:%d" % cameraAddress[1])

    def _add_timerstr(self, img):
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        color = (255, 255, 255)
        if numpy.mean(img[700:780, 900:950]) > 128:
            color = (0, 0, 0)
        cv2.putText(img, time_str, (400, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return img

    def _processImage(self, q, client):
        client.send(struct.pack("lhh", self.src, self.resolution[0], self.resolution[1]))
        while(1):
            try:
                info = struct.unpack("lhh", client.recv(12))
                bufSize = info[0]
            except struct.error:
                self.stopflag = 1
                client.close()
                cv2.destroyAllWindows()
                print("socket broken!")
                break

            if bufSize:
                try:
                    self.mutex.acquire()
                    self.buf = b''
                    tempBuf = self.buf
                    while(bufSize):                     # 循环读取到一张图片的长度
                        tempBuf = client.recv(bufSize)
                        bufSize -= len(tempBuf)
                        self.buf += tempBuf
                        data = numpy.fromstring(self.buf, dtype='uint8')
                        self.image = cv2.imdecode(data, 1)
                    # cv2.imshow(self.name, self.image)
                    q.get_nowait() if q.full() else None
                    q.put_nowait(self.image)
                    print("ImageProcessing")
                except:
                    print("receive failed")
                    pass
                finally:
                    self.mutex.release()
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        client.close()
                        cv2.destroyAllWindows()
                        print("give up connecting")
                        return


    def getData(self, q, client):
        showThread = threading.Thread(target=self._processImage, args=(q, client,
                                                                            ))
        saveThread = threading.Thread(target=self.saveVideoLocal, args=(60, q,
                                                                        ))
        showThread.setDaemon(True)
        saveThread.setDaemon(True)

        saveThread.start()
        showThread.start()

    def setWindowName(self, name):
        self.name = name


    def saveVideoLocal(self, back_up, q):
        videocount = 0
        framecount = 0
        out = cv2.VideoWriter('saveVideo/' + 'No.' + str(videocount) + '.avi', self.fourcc, 20.0, (640, 480))
        path = os.getcwd() + "/" + "saveVideo"
        while(1):
            print("SaveProcessing")
            frame = q.get()
            try:
                self.mutex.acquire()
                self._add_timerstr(frame)
                if videocount >= 60:
                    videocount = 0
                else:
                    if framecount <= (back_up * 100):
                        out.write(frame)
                        framecount += 1
                    else:
                        out.release()
                        framecount = 0
                        videocount += 1
                        out = cv2.VideoWriter('saveVideo/' + 'No.' + str(videocount) + '.avi', self.fourcc, 15.0, (640, 480))
                        out.write(frame)
            except:
                pass
            finally:
                self.mutex.release()
                if (self.stopflag == 1):
                    out.release()
                    return

    def run(self):
        while(1):
            q = Queue(maxsize=6000)
            print("waiting for connection...")
            cameraClient, addr = self.socket.accept()
            self.stopflag = 0
            showThread = threading.Thread(target=self._processImage, args=(q, cameraClient,
                                                                           ))
            saveThread = threading.Thread(target=self.saveVideoLocal, args=(60, q,
                                                                            ))
            showThread.setDaemon(True)
            saveThread.setDaemon(True)

            saveThread.start()
            showThread.start()


def main():
    print("Starting connection...")
    cam = webCamConnect()
    # cam.check_config()
    # print("resolution:%d * %d" % (cam.resolution[0], cam.resolution[1]))
    # print("target ip: %s:%d" % (cam.remoteAddress[0], cam.remoteAddress[1]))
    cam.run()

if __name__ == "__main__":
    main()