#!/workspaces/Anaconda/anaconda3/bin/python
# #-*-coding:utf-8 -*-

import socket
import MyThread
import threading
import struct
import os
import time
import sys
import numpy
import cv2
import re
from EmailAlarm import sendmail
from queue import Queue
import EmailCtrl
import email
import poplib
from email.parser import Parser
from email.header import decode_header
from email.utils import parseaddr

class webCamConnect:
    def __init__(self, resolution = [640, 480], clientProt = ("", 6999),
                 windowName = "video"):
        self.clientPort = clientProt
        self.setSocket(self.clientPort)
        self.resolution = resolution
        self.name = windowName
        self.mutex = threading.Lock()
        self.src = 911 + 15
        self.videoNum = 60
        self.videoLength = 50
        self.path = os.getcwd()
        self.img_quality = 15
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')
        self.stopflag = 0
        self._q = Queue(maxsize=6000)
        self.lastvideonum = 0
        self.lastcompletevideo = 0
        self.cmd = 0x00

    def setHost(self, cameraAddress):
        self.clientPort = cameraAddress

    def setImageResolution(self, resolution):
        self.resolution = resolution

    def setSocket(self, cameraAddress):
        self.mysocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.mysocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.mysocket.bind(self.clientPort)
        self.mysocket.listen(5)
        print("Listening port:%d" % cameraAddress[1])

    def _add_time(self, img):
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
            except:
                self.stopflag = 1
                client.close()
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
                    # print("ImageProcessing")
                except:
                    print("receive failed")
                    pass
                finally:
                    self.mutex.release()
                    # if cv2.waitKey(1) & 0xFF == ord('q'):
                    #     client.close()
                    #     print("give up connecting")
                    #     self.stopflag = 2
                    #     return


    def setWindowName(self, name):
        self.name = name


    def _saveVideoLocal(self, videoNum, queue):
        videocount = 0
        framecount = 0
        out = cv2.VideoWriter('saveVideo/' + 'No.' + str(videocount) + '.avi', self.fourcc, 20.0, (640, 480))
        path = os.getcwd() + "/" + "saveVideo"
        while(1):
            # print("SaveProcessing")
            frame = queue.get()
            if (self.stopflag != 0):
                self.videoNum = videocount
                out.release()
                break
            try:
                # self.mutex.acquire()
                self._add_time(frame)
                if videocount >= self.videoNum:
                    videocount = 0
                else:
                    if framecount <= (self.videoLength * 100):
                        out.write(frame)
                        framecount += 1
                    else:
                        out.release()
                        framecount = 0
                        self.lastcompletevideo = videocount
                        videocount += 1
                        self.lastvideonum = videocount
                        out = cv2.VideoWriter('saveVideo/' + 'No.' + str(videocount) + '.avi', self.fourcc, 15.0, (640, 480))
                        out.write(frame)
            except:
                pass
            finally:
                # self.mutex.release()
                if (self.stopflag != 0):
                    out.release()
                    break


    def check_config(self):
        path = os.getcwd()
        print(path)
        if os.path.isfile('video_config.txt') is False:
            f = open("video_config.txt", 'w+')
            print("w = %d, h = %d" %(self.resolution[0], self.resolution[1]), file=f)
            # print("IP is %s:%d" %(self.clientPort[0], self.clientPort), file=f)
            print("Save video flag: %d(number of video), %d(length of video(num*100 frame))" % (self.videoNum, self.videoLength), file=f)
            print("image's quality is:%d, range(0~95)" %(self.img_quality), file=f)
            f.close()
            print("Config Initialized")
        else:
            print("Reading Config...")
            f = open("video_config.txt", 'r+')
            tmp_data = f.readline(50)   # 1 resolution
            num_list = re.findall(r"\d+", tmp_data)
            self.resolution[0] = int(num_list[0])
            self.resolution[1] = int(num_list[1])
            # tmp_data = f.readline(50)   # 2 ip, port
            # num_list = re.findall(r"\d+", tmp_data)
            # str_tmp = "%d.%d.%d.%d" %(int(num_list[0]), int(num_list[1]), int(num_list[2]), int(num_list[3]))
            # self.remoteAddress = (str_tmp, int(num_list[4]))
            tmp_data = f.readline(80)   # 3 savedata_flag
            num_list = re.findall(r"\d+", tmp_data)
            self.videoNum = int(num_list[0])
            self.videoLength = int(num_list[1])
            tmp_data = f.readline(50)   # 3 savedata_flag
            # print(temp_data)
            self.img_quality = int(re.findall(r"\d+", tmp_data)[0])
            print('Image quality is:', self.img_quality, '(range 0-95)')
            self.src = 911 + self.img_quality
            f.close()


    def _breaklog(self, stopflag):
        while(1):
            if self.stopflag:
                print("Recording erro log")
                f = open("connection log.txt", 'a+')
                print("Socket broken at:%s" % time.strftime("%Y-%m-%d %H:%M:%S",
                                              time.localtime(time.time())), file=f)

                print("ERROR CODE[%d]" %(self.stopflag), end='-', file=f)
                if (self.stopflag == 1):
                    print("Socket broken", file=f)
                elif (self.stopflag == 2):
                    print("Give up connection", file=f)
                print("/--------------------------END-------------------------/", file=f)
                f.close()
                self.stopflag = 0
                while(sendmail(messagesub="Connection broken log", videonum=("No." + str(self.lastvideonum)), txtname="connection log.txt")):
                    pass
                break




    def _proceeding(self):
        threads = []
        funcs = [self._processImage, self._saveVideoLocal, self._breaklog, self._emailCrtl]
        nfuncs = len(funcs)
        args = [(self._q, self._cameraClient), (self.videoNum, self._q), (1, ), (1, 2)]
        names = ['getpicture', 'save', 'log', 'emailctrl']

        for i in range(nfuncs):
            t = MyThread.MyThread(func=funcs[i], name=names[i], args=args[i])
            threads.append(t)
        for i in range(nfuncs):
            if(i < 2):
                threads[i].setDaemon(True)
        for i in range(nfuncs):
            threads[i].start()

    def _emailCrtl(self, a, b):
        msgcount = 0
        while (1):
            try:
                emailctrl = EmailCtrl.EmailCtrl(email="995450215@qq.com", password="qshkxonirqjsbcef",
                                                pop3_server="pop.qq.com")
                emailctrl.emailServerConnect()
                msgnum = len(emailctrl.emailserver.list()[-2])
                if msgnum != msgcount:
                    msgcount = msgnum
                    info = emailctrl.getcmd()
                    if info[0][1] == '17683740622@163.com':
                        self.cmd = info[1]
                        print('Got cmd:', self.cmd)
                        self._cmd_protocol()
            except Exception:
                print("Error: Conected emailserver failed.")
            finally:
                pass

            try:
                emailctrl.emailServerDisconnect()
            except Exception:
                print("Error: Disconected emailserver failed.")
            finally:
                time.sleep(10)

    def _cmd_protocol(self):

        if self.cmd == 0:
            pass
        elif self.cmd == '1':
            while (sendmail(messagesub="Connection broken log", videonum=("No." + str(self.lastvideonum)),
                            txtname="connection log.txt")):
                pass
        elif self.cmd == '2':
            while (sendmail(messagesub="Last Video", videonum=("No." + str(self.lastvideonum)),
                            txtname=None)):
                pass
        elif self.cmd == '3':
            while (sendmail(messagesub="Last Complete Video", videonum=("No." + str(self.lastcompletevideo)),
                            txtname=None)):
                pass
        elif self.cmd == 4:
            pass
        else:
            pass



    def startrun(self):
        while(1):
            self._cameraClient, addr = self.mysocket.accept()
            f = open("connection log.txt", 'a')
            print("/-------------------------START------------------------/", file=f)
            print("Get connection at:%s" % time.strftime("%Y-%m-%d %H:%M:%S",
                                              time.localtime(time.time())), file=f)
            print("Socket info:%s:%d" % (self._cameraClient, self.clientPort[1]), file=f)
            f.close()
            self._proceeding()


def main():
    print("Starting connection...")
    cam = webCamConnect()
    cam.check_config()
    cam.startrun()

if __name__ == "__main__":
    main()