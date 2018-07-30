#!/usr/bin/env python

import getopt
import logging
import sys

import yappi

from gbrick import utils as util
from gbrick import define as Define
from gbrick.gncontroller import GNControllerService

G_END = '\033[0m'
G_START = '\033[1m'
G_YELLOW = G_START+'\033[33m'
G_PURPLE = G_START+'\033[35m'

def main(argv):
    logging.info("GNController got argv(list): " + str(argv))

    try:
        opts, args = getopt.getopt(argv, "dhp:o:s:",
                                   ["help",
                                    "port=",
                                    "configure_file_path=",
                                    ])
    except getopt.GetoptError as e:
        logging.error(e)
        usage()
        sys.exit(1)

    # apply json configure values
    for opt, arg in opts:
        if (opt == "-o") or (opt == "--configure_file_path"):
            Define.Configure().load_configure_json(arg)

    # apply default configure values
    port = Define.PORT_GNC
    cert = None
    pw = None
    seed = None

    # apply option values
    for opt, arg in opts:
        if opt == "-d":
            util.set_log_level_debug()
        elif (opt == "-p") or (opt == "--port"):
            port = arg
        elif (opt == "-h") or (opt == "--help"):
            usage()
            return

    # Check Port is Using
    if util.check_port_using(Define.IP_GNC, int(port)):
        logging.error('GNController Service Port is Using '+str(port))
        return

    GNControllerService(Define.IP_GNC, cert, pw, seed).serve(port)


def usage():
    print(G_YELLOW+"USAGE: gbrick GNController Service")
    print("python3 gncontroller.py [option] [value].... ")
    print("[   GNController  Option   ]"+G_END)
    print(G_PURPLE+"\t-p or --port : Port of GNController Service")
    print("\t-h or --help : usage")
    print("\t-d : Colored log on display"+G_END)


# Run grpc server
if __name__ == "__main__":
    try:
        util.create_default_pki()

        if Define.ENABLE_PROFILING:
            yappi.start()
            main(sys.argv[1:])
            yappi.stop()
        else:
            main(sys.argv[1:])
    except KeyboardInterrupt:
        if Define.ENABLE_PROFILING:
            yappi.stop()
            print('Yappi result (func stats) ======================')
            yappi.get_func_stats().print_all()
            print('Yappi result (thread stats) ======================')
            yappi.get_thread_stats().print_all()
