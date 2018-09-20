from gbrick.wagon.wagon import *
from gbrick.consensus.llfc.llfc import *
from gbrick.blockchain.blockchain import *


if __name__ == '__main__':
    # module
    llfc = LLFCEngine()
    p2p = P2P()

    hub = ModuleHub()
    hub.set_module(ModuleType.CONSENSUS, llfc)
    hub.set_module(ModuleType.P2P, p2p)

    llfc.set_hub(hub)
    p2p.set_hub(hub)

    # singleton
    BlockChain().start()
    Wagon().start()
    llfc.start()
    p2p.start()

