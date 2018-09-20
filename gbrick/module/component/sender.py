import zmq


class Sender:
    def __init__(self, ip: str, port: str, sender_id: bytes):
        self.socket = zmq.Context().socket(zmq.DEALER)
        self.socket.setsockopt(zmq.IDENTITY, sender_id)
        self.socket.connect("tcp://{0}:{1}".format(ip, port))

    def send(self, str_message: str) -> str:
        self.socket.send_string(str_message)
        response = self.socket.recv().decode('utf-8')
        return response

    def push(self, str_message: str):
        self.socket.send_string(str_message)
