import threading
from time import sleep, ctime

class MyThread(threading.Thread):

    def __init__(self, func, name='', args=()):
        threading.Thread.__init__(self)
        self.name = name
        self.func = func
        self.args = args

    def run(self):
        print('Start thread:%s at %s' %(self.name, ctime()))
        self.func(*self.args)
        print('Thread:%s finished at %s' % (self.name, ctime()))

