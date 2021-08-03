"""
This is a message passing server.
It will be used in inter process communication
for sonyc
"""
from multiprocessing.managers import BaseManager
import Queue

__author__ = "Mohit Sharma"
__version__ = "Development"

queue = Queue.Queue()


class QueueManager(BaseManager):
    pass

QueueManager.register('get_queue', callable=lambda: queue)
qMan = QueueManager(address=('', 62877), authkey='cusp@sonyc')  #Mcusp
server = qMan.get_server()
server.serve_forever()
