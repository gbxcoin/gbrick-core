'''
name            : gbrick::define_code.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180211
date_modified   : 20180701
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

from enum import IntEnum

class Method:
    request = "Request"


class Request(IntEnum):
    status = 1
    stop = -9

    glogic_load = 200
    glogic_invoke = 201
    glogic_query = 202
    glogic_set = 203  # just for test, set glogic by peer_service
    glogic_connect = 204  # make stub of peer_service on glogic_service for IPC

    peer_peer_list = 600
    peer_get_leader = 601  # get leader peer object
    peer_complain_leader = 602  # complain leader peer is no response
    peer_reconnect_to_rs = 603  # reconnect to rs when rs restart detected.

    rs_get_configuration = 800
    rs_set_configuration = 801
    rs_send_channel_manage_info_to_rs = 802

    tx_create = 900  # create tx to inner tx service
    tx_connect_to_leader = 901  # connect to leader
    tx_connect_to_inner_peer = 902  # connect to mother peer service in same inner gRPC micro service network

    broadcast_subscribe = 1000  # subscribe for broadcast
    broadcast_unsubscribe = 1001  # unsubscribe for broadcast
    broadcast = 1002  # broadcast message


class MetaParams:
    class GlogicLoad:
        repository_path = "repository_path"
        glogic_package = "glogic_package"
        base = "base"
        peer_id = "peer_id"

    class GlogicInfo:
        glogic_id = "glogic_id"
        glogic_version = "glogic_version"


# gRPC Response Code ###
class Response(IntEnum):
    success = 0
    success_validate_block = 1
    success_announce_block = 2
    fail = -9000
    fail_validate_block = -9001
    fail_announce_block = -9002
    fail_wrong_block_hash = -9003
    fail_no_leader_peer = -9004
    fail_validate_params = -9005
    fail_made_block_count_limited = -9006
    fail_wrong_subscribe_info = -9007
    fail_connect_to_leader = -9008
    fail_add_tx_to_leader = -9009
    fail_no_peer_info_in_rs = -9500
    timeout_exceed = -9900
    not_treat_message_code = -9999


responseCodeMap = {
    Response.success:                   (Response.success,                      "success"),
    Response.success_validate_block:    (Response.success_validate_block,       "success validate block"),
    Response.success_announce_block:    (Response.success_announce_block,       "success announce block"),
    Response.fail:                      (Response.fail,                         "fail"),
    Response.fail_validate_block:       (Response.fail_validate_block,          "fail validate block"),
    Response.fail_announce_block:       (Response.fail_announce_block,          "fail announce block"),
    Response.fail_wrong_block_hash:     (Response.fail_wrong_block_hash,        "fail wrong block hash"),
    Response.fail_no_leader_peer:       (Response.fail_no_leader_peer,          "fail no leader peer"),
    Response.fail_validate_params:      (Response.fail_validate_params,         "fail validate params"),
    Response.fail_wrong_subscribe_info: (Response.fail_wrong_subscribe_info,    "fail wrong subscribe info"),
    Response.fail_connect_to_leader:    (Response.fail_connect_to_leader,       "fail connect to leader"),
    Response.fail_add_tx_to_leader:     (Response.fail_add_tx_to_leader,        "fail add tx to leader"),
    Response.fail_no_peer_info_in_rs:   (Response.fail_no_peer_info_in_rs,      "fail no peer info in radio station"),
    Response.timeout_exceed:            (Response.timeout_exceed,               "timeout exceed")
}


def get_response_code(code):
    return responseCodeMap[code][0]


def get_response_msg(code):
    return responseCodeMap[code][1]


def get_response(code):
    return responseCodeMap[code][0], responseCodeMap[code][1]
