import zmq
from abc import *
from threading import *


class IReceiveDelegator(metaclass=ABCMeta):
    @abstractmethod
    def receiver_pre_run(self, receiver): raise NotImplementedError

    @abstractmethod
    def receiver_end_run(self, receiver): raise NotImplementedError

    @abstractmethod
    def receiver_receive(self, receiver, json_message: str) -> str: raise NotImplementedError


class Receiver:
    def __init__(self, port: str, delegator: IReceiveDelegator):
        self.context = zmq.Context()
        self.router = self.context.socket(zmq.ROUTER)
        self.router.bind('tcp://*:{0}'.format(port))
        self.backend = self.context.socket(zmq.DEALER)
        self.backend.bind('inproc://backend')
        self.delegator = delegator
        self.dict_dealer = {}
        self.is_run = False
        self.port = port

    def start(self, num_threading: int=None):
        if self.is_run is True:
            raise BaseException('Receiver already running')

        print('[LOG] Receiver::start: port: {0}'.format(self.port))
        self.is_run = True
        ths = []
        if num_threading is None:
            num_threading = 1

        for i in range(0, num_threading):
            th = Thread(target=self.start_to_receive, args=str(i))
            #th.daemon = True
            th.start()
            ths.append(th)

        zmq.proxy(self.router, self.backend)

        for th in ths:
            th.join()

        self.router.close()
        self.backend.close()
        self.context.term()

    def start_to_receive(self, process_id):
        self.delegator.receiver_pre_run(self)
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://backend')
        while self.is_run:
            try:
                p_id, received_message = worker.recv_multipart()
                response = self.delegator.receiver_receive(self, json_message=received_message)
                if response is None:
                    response = 'S000'
                worker.send_multipart([p_id, response.encode('utf-8')])
            except Exception as e:
                print('[ERROR]Receiver::start_to_receive: {0}'.format(e))
                worker.send_multipart([p_id, "F001".encode('utf-8')])
                raise e
        self.delegator.receiver_end_run(self)


class ReceiverNoResponse(Receiver):
    def __init__(self, port:str, delegator: IReceiveDelegator):
        super().__init__(port=port, delegator=delegator)

    def start(self, num_threading: int=None):
        super().start(num_threading=num_threading)

    def start_to_receive(self, process_id):
        self.delegator.receiver_pre_run(self)
        worker = self.context.socket(zmq.DEALER)
        worker.connect('inproc://backend')
        while self.is_run:
            try:
                p_id, received_message = worker.recv_multipart()
                self.delegator.receiver_receive(self, json_message=received_message)
            except Exception as e:
                print('[ERROR]ReceiverNoResponse::start_to_receive: {0}'.format(e))
                raise e
        self.delegator.receiver_end_run(self)


