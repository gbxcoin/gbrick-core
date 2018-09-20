import queue
from threading import *
from abc import *


class IMessageQueueDelegator(metaclass=ABCMeta):
    @abstractmethod
    def mq_process_queue(self, queue_thread, message): raise NotImplementedError

    @abstractmethod
    def mq_process_synced(self, queue_thread): raise NotImplementedError

    @abstractmethod
    def mq_pre_run(self, queue_thread): raise NotImplementedError

    @abstractmethod
    def mq_end_run(self, queue_thread): raise NotImplementedError


class MessageQueue:
    def __init__(self, delegator: IMessageQueueDelegator):
        self.queue = queue.Queue()
        self.delegator = delegator
        self.is_running = False

    def start(self):
        if self.is_running is True:
            raise BaseException('QueueThread is already running')

        self.is_running = True
        th = Thread(target=self.start_to_process)
        #th.daemon = True
        th.start()

    def start_to_process(self):
        self.delegator.mq_pre_run(self)
        while self.is_running:
            try:
                while self.queue.qsize() > 0:
                    message = self.queue.get()
                    self.delegator.mq_process_queue(self, message=message)
                self.delegator.mq_process_synced(self)
            except Exception as e:
                raise e

        self.delegator.mq_end_run(self)

    def push(self, message):
        self.queue.put(message)