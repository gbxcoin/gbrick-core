#!/usr/bin/env python

import sys
import os
import logging
import getopt
import yappi
from gbrick import utils as util
from gbrick import define as conf
from gbrick.peer import PeerService
from gbrick.base import ObjectManager

G_END = '\033[0m'
G_START = '\033[1m'
G_YELLOW = G_START+'\033[33m'
G_PURPLE = G_START+'\033[35m'

def main(argv):
    # logging.debug("Peer main got argv(list): " + str(argv))

    try:
        opts, args = getopt.getopt(argv, "dhr:p:o:",# c:
                                   ["help",
                                    "gnc_target=",
                                    "port=",
                                    #"glogic=",
                                    "configure_file_path=",
                                    ])
    except getopt.GetoptError as e:
        logging.error(e)
        usage()
        sys.exit(1)

    # apply json configure values
    for opt, arg in opts:
        if (opt == "-o") or (opt == "--configure_file_path"):
            conf.Configure().load_configure_json(arg)

    # apply default configure values
    port = conf.PORT_PEER
    gnc_ip = conf.IP_GNC
    gnc_port = conf.PORT_GNC
    gnc_ip_sub = conf.IP_GNC
    gnc_port_sub = conf.PORT_GNC
    glogic = conf.DEFAULT_GLOGIC_PACKAGE
    public = conf.PUBLIC_PATH
    private = conf.PRIVATE_PATH
    pw = conf.DEFAULT_PW

    # Parse command line arguments.
    for opt, arg in opts:
        if (opt == "-r") or (opt == "--gnc_target"):
            try:
                if ':' in arg:
                    target_list = util.parse_target_list(arg)
                    if len(target_list) == 2:
                        gnc_ip, gnc_port = target_list[0]
                        gnc_ip_sub, gnc_port_sub = target_list[1]
                    else:
                        gnc_ip, gnc_port = target_list[0]
                    # util.logger.spam(f"peer "
                    #                  f"gnc_ip({gnc_ip}) "
                    #                  f"gnc_port({gnc_port}) "
                    #                  f"gnc_ip_sub({gnc_ip_sub}) "
                    #                  f"gnc_port_sub({gnc_port_sub})")
                elif len(arg.split('.')) == 4:
                    gnc_ip = arg
                else:
                    raise Exception("Invalid IP format")
            except Exception as e:
                util.exit_and_msg(f"'-r' or '--gnc_target' option requires "
                                  f"[IP Address of GNC]:[PORT number of GNC], "
                                  f"or just [IP Address of GNC] format. error({e})")
        elif (opt == "-p") or (opt == "--port"):
            port = arg
        #elif (opt == "-c") or (opt == "--glogic"):
         #   glogic = arg
        elif opt == "-d":
            util.set_log_level_debug()
        elif (opt == "-h") or (opt == "--help"):
            usage()
            return

    # run peer service with parameters
    logging.info(f"gbrick peer run with: port({port}) "
                 f"GNC({gnc_ip}:{gnc_port}) "
                 f"glogic({glogic})")

    # check Port Using
    if util.check_port_using(conf.IP_PEER, int(port)):
        util.exit_and_msg('Peer Service Port is Using '+str(port))

    # str password to bytes
    if isinstance(pw, str):
        pw = pw.encode()

    ObjectManager().peer_service = PeerService(gnc_ip=gnc_ip,
                                               gnc_port=gnc_port,
                                               public_path=public,
                                               private_path=private,
                                               cert_pass=pw)

    # logging.debug("gbrick peer_service is: " + str(ObjectManager().peer_service))
    ObjectManager().peer_service.serve(port, glogic)


def usage():
    print(G_YELLOW+"USAGE: gbrick Peer Service")
    print("python3 peer.py [option] [value] ....")
    print("[   Peer Option   ]"+G_END)
    print(G_PURPLE+"\t-o or --configure_file_path : json config file path")
    print("\t-h or --help : usage")
    print("\t-r or --gnc_target : [IP Address of GNC]:[PORT number of GNC]")
    print("\t-p or --port : port of Peer Service")
    #print("-c or --glogic : user glogic repository Path")
    print("\t-d : Colored log on display"+G_END)


# Run grpc server as a Peer
if __name__ == "__main__":
    try:
        if os.getenv('DEFAULT_GLOGIC_HOST') is not None:
            os.system("ssh-keyscan "+os.getenv('DEFAULT_GLOGIC_HOST')+" >> /root/.ssh/known_hosts")

        if conf.ENABLE_PROFILING:
            yappi.start()
            main(sys.argv[1:])
            yappi.stop()
        else:
            main(sys.argv[1:])
    except KeyboardInterrupt:
        if conf.ENABLE_PROFILING:
            yappi.stop()
            print('Yappi result (func stats) ======================')
            yappi.get_func_stats().print_all()
            print('Yappi result (thread stats) ======================')
            yappi.get_thread_stats().print_all()
