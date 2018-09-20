from gbrick.module.component.gbrickprofile import *
from gbrick.module.component.receiver import *
from gbrick.module.component.sender import *
from gbrick.module.component.modulehub import *
from gbrick.gncontroller.peerinfo import *
from gbrick.module.component.messagequeue import *
from gbrick.property import *


class P2P(IReceiveDelegator, IMessageQueueDelegator, IModule):
    def __init__(self):
        self.profile = GbrickProfile().loads(PROFILE_PATH)

        self.receiver = ReceiverNoResponse(port=self.profile.peer_port, delegator=self)
        self.queue = MessageQueue(self)
        self.hub = None

        self.dict_peer_rep = {}
        self.dict_peer_normal = {}
        self.dict_module = {}

    def start(self):
        self.queue.start()
        self.receiver.start(10)

    # IModule Implementation
    def set_hub(self, hub):
        self.hub = hub

    def push(self, message: Message):
        self.queue.push(message)

    # dict_params: additional parameters
    def add_peer(self, p_peer_info: PeerInfo, dict_params: dict=None):
        sender: Sender = Sender(ip=p_peer_info.ip, port=p_peer_info.port, sender_id=p_peer_info.id)
        if p_peer_info.type == NodeType.REP:
            self.dict_peer_rep.__setitem__(p_peer_info.id, sender)
        elif p_peer_info.type == NodeType.NORMAL:
            self.dict_peer_normal.__setitem__(p_peer_info.id, sender)
        else:
            print('[ERROR] P2P::add_peer: unknown nodetype {0}'.format(p_peer_info.type))

    # IReceiveDelegator Implementation =============================================
    def receiver_pre_run(self, receiver):
        print('[LOG] P2P::receiver_pre_run')

    def receiver_end_run(self, receiver):
        print('[LOG] P2P::receiver_end_run')

    def receiver_receive(self, receiver, json_message: str) -> str:
        self.queue.push(Message(p_json_str=json_message))
        return
    # ==============================================================================

    # IMessageQueueDelegator Implementation ========================================
    def mq_process_queue(self, queue_thread, message):
        print('[LOG] P2P::mq_process_queue: {0}'.format(message.to_dict()))

        if message.to == ModuleType.P2P:
            dict_peer = {}
            if message.type == MessageType.BROADCAST_REP:
                self.broadcast(message.data, self.dict_peer_rep)
            elif message.type == MessageType.BROADCAST_NORMAL:
                self.broadcast(message.data, self.dict_peer_normal)
            elif message.type == MessageType.ADD_PEER:
                for i in message.data.get('list_node'):
                    self.add_peer(PeerInfo(p_dict=i))

                return

            for k in dict_peer:
                sender = dict_peer.get(k)
                sender.push(message.data)
            return
        else:
            self.hub.push(message)

    def mq_process_synced(self, queue_thread): pass

    def mq_pre_run(self, queue_thread): pass

    def mq_end_run(self, queue_thread): pass
    # ==============================================================================

    def broadcast(self, message: str, dict_peer_target: dict):
        for k in dict_peer_target:
            sender: Sender = dict_peer_target.get(k)
            #sender.push(message)
            Thread(target=sender.push, args=(message,)).start()


if __name__ == '__main__':
    p = P2P()
    p.start()
