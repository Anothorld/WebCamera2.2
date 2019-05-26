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
# 接受过程太慢且存在掉帧！后续还需加上断开邮件提示

class webCamConnect:
    def __init__(self, resolution = [640, 480], remoteAddress = ("10.10.20.40", 7999),
                 windowName = "video"):
        self.remoteAddress = remoteAddress
        self.resolution = resolution
        self.name = windowName
        self.mutex = threading.Lock()
        self.src = 911 + 15
        self.interval = 0
        self.back_up = 0
        self.path = os.getcwd()
        self.img_quality = 15
        self.fourcc = cv2.VideoWriter_fourcc(*'XVID')

    def _setSocket(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    def connect(self):
        self._setSocket()
        self.socket.connect(self.remoteAddress)

    def _add_timerstr(self, img):
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        color = (255, 255, 255)
        if numpy.mean(img[700:780, 900:950]) > 128:
            color = (0, 0, 0)
        cv2.putText(img, time_str, (400, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        return img

    def _processImage(self, q):
        self.socket.send(struct.pack("lhh", self.src, self.resolution[0], self.resolution[1]))
        while(1):
            info = struct.unpack("lhh", self.socket.recv(12))
            bufSize = info[0]
            if bufSize:
                ticks = time.time()
                try:
                    self.mutex.acquire()
                    self.buf = b''
                    tempBuf = self.buf
                    while(bufSize):                     # 循环读取到一张图片的长度
                        tempBuf = self.socket.recv(bufSize)
                        bufSize -= len(tempBuf)
                        self.buf += tempBuf
                        data = numpy.fromstring(self.buf, dtype='uint8')
                        self.image = cv2.imdecode(data, 1)
                    cv2.imshow(self.name, self.image)
                    q.get_nowait() if q.full() else None
                    q.put_nowait(self.image)
                except:
                    print("receive failed")
                    pass
                finally:
                    self.mutex.release()
                    print("Camera:", time.time() - ticks)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        self.socket.close()
                        cv2.destroyAllWindows()
                        print("give up connecting")
                        break


    def getData(self, interval, q):
        showThread = threading.Thread(target=self._processImage, args=(q,
                                                                            ))
        saveThread = threading.Thread(target=self.saveVideoLocal, args=(60, q,
                                                                        ))
        showThread.setDaemon(1)
        saveThread.setDaemon(1)
        showThread.start()
        saveThread.start()
        # saveThread.join()
        # showTread.join()

    def setWindowName(self, name):
        self.name = name

    def setRemoteAddress(self, remoteAddress):
        self.remoteAddress = remoteAddress

    def savePicToLocal(self, interval):
        while(1):
            try:
                self.mutex.acquire()
                path = os.getcwd() + "/" + "savePic"
                if not os.path.exists(path):
                    os.mkdir(path)
                cv2.imwrite("savePic/" + time.strftime("%Y%m%d-%H%M%S",
                                                        time.localtime(time.time())) + ".jpg", self.image)
            except:
                pass
            finally:
                self.mutex.release()

    def saveVideoLocal(self, back_up, q):
        videocount = 0
        framecount = 0
        out = cv2.VideoWriter('saveVideo/' + 'No.' + str(videocount) + '.avi', self.fourcc, 20.0, (640, 480))
        path = os.getcwd() + "/" + "saveVideo"
        while(1):
            try:
                frame = q.get_nowait()
            except:
                continue
            try:
                tick = time.time()
                # self.mutex.acquire()
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
                print("Save:", time.time() - tick)
                pass

    def check_config(self):
        path = os.getcwd()
        print(path)
        if os.path.isfile('video_config.txt') is False:
            f = open("video_config.txt", 'w+')
            print("w = %d, h = %d" %(self.resolution[0], self.resolution[1]), file=f)
            print("IP is %s:%d" %(self.remoteAddress[0], self.remoteAddress[1]), file=f)
            print("Save pic flag:%d" %(self.interval), file=f)
            print("image's quality is:%d, range(0~95)" %(self.img_quality), file=f)
            f.close()
            print("Config Initialized")
        else:
            f = open("video_config.txt", 'r+')
            tmp_data = f.readline(50)   # 1 resolution
            num_list = re.findall(r"\d+", tmp_data)
            self.resolution[0] = int(num_list[0])
            self.resolution[1] = int(num_list[1])
            tmp_data = f.readline(50)   # 2 ip, port
            num_list = re.findall(r"\d+", tmp_data)
            str_tmp = "%d.%d.%d.%d" %(int(num_list[0]), int(num_list[1]), int(num_list[2]), int(num_list[3]))
            self.remoteAddress = (str_tmp, int(num_list[4]))
            tmp_data = f.readline(50)   # 3 savedata_flag
            self.interval = int(re.findall(r"\d", tmp_data)[0])
            tmp_data = f.readline(50)   # 3 savedata_flag
            #print(temp_data)
            self.img_quality = int(re.findall(r"\d+", tmp_data)[0])
            #print(self.img_quality)
            self.src = 911 + self.img_quality
            f.close()
            print("Reading Config")

def main():
    q = Queue(maxsize=6000)
    print("Starting connection...")
    cam = webCamConnect()
    cam.check_config()
    print("resolution:%d * %d" %(cam.resolution[0], cam.resolution[1]))
    print("target ip: %s:%d" %(cam.remoteAddress[0], cam.remoteAddress[1]))
    cam.connect()
    cam.getData(cam.interval, q)


if __name__ == "__main__":
    main()
    print("mainDone")




