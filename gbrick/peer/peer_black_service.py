
'''
name            : gbrick::defult.py
description     : Gbrick Blockchain
author          : Steve Han
date_created    : 20180205
date_modified   : 20180710
version         : 0.1
python_version  : 3.6.5
Comments        :
'''

import re

import grpc
from grpc._channel import _Rendezvous

from gbrick.base import ObjectManager
from gbrick.blockchain import *
from gbrick.protos import gbrick_pb2_grpc
from gbrick.utils import define_code


import gbrick_pb2

# if platform.system() == 'Darwin':
#     sys.path.insert(0, "/Users/hangs/Documents/source/blockchain/gbrick_coin/gbrick/protos")
#     sys.path.append('../')
#     import gbrick_pb2
# else:
#     from gbrick.proto import gbrick_pb2

class BlackOuterService(gbrick_pb2_grpc.PeerServiceServicer):
    """secure gRPC service for outer Client or other Peer
    """

    def __init__(self):
        self.__handler_map = {
            define_code.Request.status: self.__handler_status,
            define_code.Request.peer_peer_list: self.__handler_peer_list
        }

    @property
    def peer_service(self):
        return ObjectManager().peer_service

    def __handler_status(self, request, context):
        util.logger.debug(f"peer_outer_service:handler_status")
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        status = dict()
        if ObjectManager().peer_service is not None:
            status['peer_type'] = \
                str(self.peer_service.channel_manager.get_block_manager(channel_name).peer_type)
        else:
            status['peer_type'] = '0'
        status_json = json.dumps(status)

        return gbrick_pb2.Message(code=define_code.Response.success, meta=status_json)

    def __handler_peer_list(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        peer_manager = self.peer_service.channel_manager.get_peer_manager(channel_name)
        message = "All Group Peers count: " + str(len(peer_manager.peer_list[Define.ALL_GROUP_ID]))

        return gbrick_pb2.Message(
            code=define_code.Response.success,
            message=message,
            meta=str(peer_manager.peer_list))

    def Request(self, request, context):
        # util.logger.debug(f"Peer Service got request({request.code})")

        if request.code in self.__handler_map.keys():
            return self.__handler_map[request.code](request, context)

        return gbrick_pb2.Message(code=define_code.Response.not_treat_message_code)

    def GetStatus(self, request, context):
        """
        :param request:
        :param context:
        :return:
        """
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug("Peer GetStatus : %s", request)
        peer_status = self.peer_service.common_service.getstatus(
            self.peer_service.channel_manager.get_block_manager(channel_name))

        return gbrick_pb2.StatusReply(
            status=json.dumps(peer_status),
            block_height=peer_status["block_height"],
            total_tx=peer_status["total_tx"],
            is_leader_complaining=peer_status['leader_complaint'])

    def GetglogicStatus(self, request, context):
        """
        :param request:
        :param context:
        :return:
        """
        logging.debug("Peer GetglogicStatus request : %s", request)
        glogic_status = json.loads("{}")
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        try:
            glogic_status_response = self.peer_service.channel_manager.get_glogic_container_stub(channel_name).call(
                "Request",
                gbrick_pb2.Message(code=define_code.Request.status)
            )
            logging.debug("Get Glogic Status : " + str(glogic_status_response))
            if glogic_status_response.code == define_code.Response.success:
                glogic_status = json.loads(glogic_status_response.meta)

        except Exception as e:
            logging.debug("Glogic Service Already stop by other reason. %s", e)

        return gbrick_pb2.StatusReply(
            status=json.dumps(glogic_status),
            block_height=0,
            total_tx=0)

    def Stop(self, request, context):

        if request is not None:
            logging.info('Peer will stop... by: ' + request.reason)

        try:
            response = self.peer_service.stub_to_glogic_service.call(
                "Request",
                gbrick_pb2.Message(code=define_code.Request.stop)
            )
            logging.debug("try stop glogic container: " + str(response))
        except Exception as e:
            logging.debug("Glogic Service Already stop by other reason. %s", e)

        self.peer_service.service_stop()
        return gbrick_pb2.StopReply(status="0")

    def Echo(self, request, context):

        return gbrick_pb2.CommonReply(response_code=define_code.Response.success,
                                      message=request.request)

    def CreateTx(self, request, context):
        """make tx by client request and broadcast it to the network

        :param request:
        :param context:
        :return:
        """
        # logging.debug(f"peer_outer_service::CreateTx request({request.data}), channel({request.channel})")

        tx = Transaction()
        # TODO
        glogic_id = ""
        glogic_version = ""
        result_code = define_code.Response.success
        more_info = ""

        if self.peer_service.glogic_info is not None:
            # logging.debug("peer_outer_service create tx is have peer service info ")
            glogic_id = self.peer_service.glogic_info[define_code.MetaParams.GlogicInfo.glogic_id]
            glogic_version = self.peer_service.glogic_info[define_code.MetaParams.GlogicInfo.glogic_version]

        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel

        tx.init_meta(self.peer_service.peer_id, glogic_id, glogic_version, channel_name)
        result_hash = tx.put_data(request.data)
        tx.sign_hash(self.peer_service.auth)
        # logging.debug("peer_outer_service result hash : " + result_hash)

        self.peer_service.send_to_process_thread.send_to_process((Define.BC_CREATE_TX_COMMAND, tx))

        return gbrick_pb2.CreateTxReply(
            response_code=result_code,
            tx_hash=result_hash,
            more_info=more_info)

    def AddTx(self, request: gbrick_pb2.TxSend, context):
        """Add tx to Block Manager

        :param request:
        :param context:
        :return:
        """
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        # logging.debug(f"peer_outer_service::AddTx channel({channel_name})")

        block_manager = self.peer_service.channel_manager.get_block_manager(channel_name)

        if block_manager.peer_type == gbrick_pb2.BLOCK_GENERATOR and block_manager.consensus.block is None:
            return gbrick_pb2.CommonReply(
                response_code=define_code.Response.fail_made_block_count_limited,
                message="this leader can't make more block")

        block_manager.add_tx_unloaded(request.tx)

        return gbrick_pb2.CommonReply(response_code=define_code.Response.success, message="success")

    def GetTx(self, request, context):
        """get transaction

        :param request: tx_hash
        :param context:
        :return:
        """
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        # logging.debug(f"peer_outer_service::GetTx channel({channel_name})")
        tx = self.peer_service.channel_manager.get_block_manager(channel_name).get_tx(request.tx_hash)

        response_code, response_msg = define_code.get_response(define_code.Response.fail)
        response_meta = ""
        response_data = ""
        response_sign = b''
        response_public_key = b''

        if tx is not None:
            response_code, response_msg = define_code.get_response(define_code.Response.success)
            response_meta = json.dumps(tx.meta)
            response_data = tx.get_data().decode(Define.PEER_DATA_ENCODING)
            response_sign = tx.signature
            response_public_key = tx.public_key

        return gbrick_pb2.GetTxReply(response_code=response_code,
                                        meta=response_meta,
                                        data=response_data,
                                        signature=response_sign,
                                        public_key=response_public_key,
                                        more_info=response_msg)

    def GetLastBlockHash(self, request, context):

        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        # Peer To Client
        block_manager = self.peer_service.channel_manager.get_block_manager(channel_name)
        last_block = block_manager.get_blockchain().last_block
        response_code, response_msg = define_code.get_response(define_code.Response.fail)
        block_hash = None

        if last_block is not None:
            response_code, response_msg = define_code.get_response(define_code.Response.success)
            block_hash = last_block.block_hash

        return gbrick_pb2.BlockReply(response_code=response_code,
                                        message=(response_msg +
                                                 (" This is for block height sync",
                                                  " This is for Test Validation")
                                                 [block_manager.peer_type == gbrick_pb2.PEER]),
                                        block_hash=block_hash)

    def GetBlock(self, request, context):

        block_hash = request.block_hash
        block = None

        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        block_manager = self.peer_service.channel_manager.get_block_manager(channel_name)

        if request.block_hash == "" and request.block_height == -1:
            block_hash = block_manager.get_blockchain().last_block.block_hash

        block_filter = re.sub(r'\s', '', request.block_data_filter).split(",")
        tx_filter = re.sub(r'\s', '', request.tx_data_filter).split(",")
        logging.debug("block_filter: " + str(block_filter))
        logging.debug("tx_filter: " + str(tx_filter))

        block_data_json = json.loads("{}")

        if block_hash != "":
            block = block_manager.get_blockchain().find_block_by_hash(block_hash)
        elif request.block_height != -1:
            block = block_manager.get_blockchain().find_block_by_height(request.block_height)

        if block is None:
            return gbrick_pb2.GetBlockReply(response_code=define_code.Response.fail_wrong_block_hash,
                                            block_hash=block_hash,
                                            block_data_json="",
                                            tx_data_json="")

        for key in block_filter:
            try:
                block_data_json[key] = str(getattr(block, key))
            except AttributeError:
                try:
                    getter = getattr(block, "get_" + key)
                    block_data_json[key] = getter()
                except AttributeError:
                    block_data_json[key] = ""

        tx_data_json_list = []
        for tx in block.confirmed_transaction_list:
            tx_data_json = json.loads("{}")
            for key in tx_filter:
                try:
                    tx_data_json[key] = str(getattr(tx, key))
                except AttributeError:
                    try:
                        getter = getattr(tx, "get_" + key)
                        tx_data_json[key] = getter()
                    except AttributeError:
                        tx_data_json[key] = ""
            tx_data_json_list.append(json.dumps(tx_data_json))

        block_hash = block.block_hash
        block_data_json = json.dumps(block_data_json)

        return gbrick_pb2.GetBlockReply(response_code=define_code.Response.success,
                                        block_hash=block_hash,
                                        block_data_json=block_data_json,
                                        tx_data_json=tx_data_json_list)

    def Query(self, request, context):

        if util.check_is_json_string(request.params):
            logging.debug(f'Query request with {request.params}')
            try:
                response_from_glogic_service = self.peer_service.stub_to_glogic_service.call(
                    method_name="Request",
                    message=gbrick_pb2.Message(code=define_code.Request.glogic_query, meta=request.params),
                    timeout=Define.GLOGIC_QUERY_TIMEOUT,
                    is_raise=True
                )
                response = response_from_glogic_service.meta
            except Exception as e:
                logging.error(f'Execute Query Error : {e}')
                if isinstance(e, _Rendezvous):

                    if e.code() == grpc.StatusCode.DEADLINE_EXCEEDED:
                        return gbrick_pb2.QueryReply(response_code=define_code.Response.timeout_exceed,
                                                     response="")
                return gbrick_pb2.QueryReply(response_code=define_code.Response.fail,
                                             response="")
        else:
            return gbrick_pb2.QueryReply(response_code=define_code.Response.fail_validate_params,
                                         response="")

        if util.check_is_json_string(response):
            response_code = define_code.Response.success
        else:
            response_code = define_code.Response.fail

        return gbrick_pb2.QueryReply(response_code=response_code,
                                        response=response)

    def GetInvokeResult(self, request, context):

        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug('GetInvokeResult')
        try:
            invoke_result = \
                self.peer_service.channel_manager.get_block_manager(channel_name).get_invoke_result(request.tx_hash)
            invoke_result_str = json.dumps(invoke_result)
            logging.debug('invoke_result : ' + invoke_result_str)
            return gbrick_pb2.GetInvokeResultReply(response_code=define_code.Response.success
                                                      , result=invoke_result_str)
        except Exception as e:
            logging.error("get invoke result error : %s", str(e))
            return gbrick_pb2.GetInvokeResultReply(response_code=define_code.Response.fail)

    def AnnounceUnconfirmedBlock(self, request, context):
        """
        :param request:
        :param context:
        :return:
        """
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug(f"peer_outer_service::AnnounceUnconfirmedBlock channel({channel_name})")
        unconfirmed_block = pickle.loads(request.block)

        logging.warning("Black Peer makes Fail validate Message by intention!")
        vote_code, message = define_code.get_response(define_code.Response.fail_validate_block)

        block_vote = gbrick_pb2.BlockVote(
            vote_code=vote_code,
            channel=channel_name,
            message=message,
            block_hash=unconfirmed_block.block_hash,
            peer_id=ObjectManager().peer_service.peer_id,
            group_id=ObjectManager().peer_service.group_id)

        self.peer_service.common_service.broadcast("VoteUnconfirmedBlock", block_vote)

        return gbrick_pb2.CommonReply(response_code=define_code.Response.success, message="success")

    def AnnounceConfirmedBlock(self, request, context):
        """
        :param request: BlockAnnounce of gbrick.proto
        :param context: gRPC parameter
        :return: CommonReply of gbrick.proto
        """
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel

        # Peer To BlockGenerator
        logging.debug("AnnounceConfirmedBlock block hash: " + request.block_hash)
        response_code, response_msg = define_code.get_response(define_code.Response.fail_announce_block)

        confirmed_block = pickle.loads(request.block)

        logging.debug(f"block \n"
                      f"peer_id({confirmed_block.peer_id})\n"
                      f"made_block_count({confirmed_block.made_block_count})\n"
                      f"is_divided_block({confirmed_block.is_divided_block})")

        if len(request.block) > 0:
            logging.warning("AnnounceConfirmedBlock without Consensus ====================")
            self.peer_service.add_unconfirm_block(request.block, channel_name)

        try:
            self.peer_service.channel_manager.get_block_manager(channel_name).confirm_block(request.block_hash)
            response_code, response_msg = define_code.get_response(define_code.Response.success_announce_block)
        except (BlockchainError, BlockInValidError, BlockError) as e:
            logging.error("AnnounceConfirmedBlock: " + str(e))

        return gbrick_pb2.CommonReply(response_code=response_code, message=response_msg)

    def BlockSync(self, request, context):
        # Peer To Peer
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.info(f"BlockSync request hash({request.block_hash}) channel({channel_name})")
        block_manager = self.peer_service.channel_manager.get_block_manager(channel_name)

        block = block_manager.get_blockchain().find_block_by_hash(request.block_hash)
        if block is None:
            return gbrick_pb2.BlockSyncReply(
                response_code=define_code.Response.fail_wrong_block_hash,
                block_height=-1,
                max_block_height=block_manager.get_blockchain().block_height,
                block=b"")

        dump = pickle.dumps(block)

        return gbrick_pb2.BlockSyncReply(
            response_code=define_code.Response.success,
            block_height=block.height,
            max_block_height=block_manager.get_blockchain().block_height,
            block=dump)

    def Subscribe(self, request, context):

        if request.peer_id == "":
            return gbrick_pb2.CommonReply(
                response_code=define_code.get_response_code(define_code.Response.fail_wrong_subscribe_info),
                message=define_code.get_response_msg(define_code.Response.fail_wrong_subscribe_info)
            )
        else:
            self.peer_service.common_service.add_audience(request)

        return gbrick_pb2.CommonReply(response_code=define_code.get_response_code(define_code.Response.success),
                                      message=define_code.get_response_msg(define_code.Response.success))

    def UnSubscribe(self, request, context):

        self.peer_service.common_service.remove_audience(request.peer_id, request.peer_target)
        return gbrick_pb2.CommonReply(response_code=0, message="success")

    def AnnounceNewPeer(self, request, context):

        # prevent to show certificate content
        # logging.info('Here Comes new peer: ' + str(request))
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        # logging.debug(f"peer outer service::AnnounceNewPeer channel({channel_name})")
        peer_manager = self.peer_service.channel_manager.get_peer_manager(channel_name)

        if len(request.peer_object) > 0:
            peer = pickle.loads(request.peer_object)

            # if self.peer_service.auth.is_secure\
            #         and self.peer_service.auth.verify_new_peer(peer, gbrick_pb2.PEER) is False:
            #
            #     logging.debug("New Peer Validation Fail")
            # else:
            #     logging.debug("Add New Peer: " + str(peer.peer_id))
            #     self.peer_service.peer_manager.add_peer(peer)
            #     logging.debug("Try save peer list...")
            #     self.peer_service.common_service.save_peer_list(self.peer_service.peer_manager)

            logging.debug("Add New Peer: " + str(peer.peer_id))

            peer_manager.add_peer(peer)
            # broadcast the new peer to the others for adding an audience
            self.peer_service.common_service.add_audience(request)

            logging.debug("Try save peer list...")
            self.peer_service.channel_manager.save_peer_manager(peer_manager, channel_name)

        self.peer_service.show_peers(channel_name)

        # Block generator makes a peer_manager block up when a new peer joins the network.
        if self.peer_service.channel_manager.get_block_manager(channel_name).peer_type is gbrick_pb2.BLOCK_GENERATOR:
            # TODO
            self.add_peer_manager_tx(channel_name)

        return gbrick_pb2.CommonReply(response_code=0, message="success")

    def add_peer_manager_tx(self, channel_name):

        tx = Transaction()
        tx.type = TransactionType.peer_list
        tx.put_meta(Define.TS_CHANNEL_KEY, channel_name)
        tx.put_meta(Define.TS_PEER_ID_KEY, self.peer_service.peer_id)
        tx.put_data(self.peer_service.channel_manager.get_peer_manager(channel_name).dump())

        self.peer_service.send_to_process_thread.send_to_process(("create_tx", tx))

        if self.peer_service.channel_manager.get_block_manager(channel_name).consensus.block is None:
            logging.debug("this leader can't make more block")

        self.peer_service.channel_manager.get_block_manager(channel_name).add_tx_unloaded(pickle.dumps(tx))

    def AnnounceDeletePeer(self, request, context):
        """delete peer by radio station heartbeat, It delete peer info over whole channels.

        :param request:
        :param context:
        :return:
        """
        # channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        # logging.debug(f"AnnounceDeletePeer peer_id({request.peer_id}) group_id({request.group_id})")
        self.peer_service.channel_manager.remove_peer(request.peer_id, request.group_id)

        return gbrick_pb2.CommonReply(response_code=0, message="success")

    def VoteUnconfirmedBlock(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        block_manager = self.peer_service.channel_manager.get_block_manager(channel_name)
        util.logger.spam(f"peer_outer_service:VoteUnconfirmedBlock ({channel_name})")

        # if Define.CONSENSUS_ALGORITHM != Define.ConsensusAlgorithm.llfc:
        if block_manager.peer_type == gbrick_pb2.PEER:
            util.logger.warning(f"peer_outer_service:VoteUnconfirmedBlock ({channel_name}) No Leader Peer!")
            return gbrick_pb2.CommonReply(
                response_code=define_code.Response.fail_no_leader_peer,
                message=define_code.get_response_msg(define_code.Response.fail_no_leader_peer))

        logging.info("Peer vote to : " + request.block_hash + " " + str(request.vote_code)
                     + f"from {request.peer_id}")

        block_manager.get_candidate_blocks().vote_to_block(
            request.block_hash, (False, True)[request.vote_code == define_code.Response.success_validate_block],
            request.peer_id, request.group_id)

        return gbrick_pb2.CommonReply(response_code=define_code.Response.success, message="success")

    def ComplainLeader(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug("ComplainLeader: " + request.message)

        self.peer_service.channel_manager.get_peer_manager(channel_name).announce_new_leader(
            request.complained_leader_id, request.new_leader_id)

        return gbrick_pb2.CommonReply(response_code=define_code.Response.success, message="success")

    def AnnounceNewLeader(self, request, context):
        channel_name = Define.GBRICK_DEFAULT_CHANNEL if request.channel == '' else request.channel
        logging.debug(f"AnnounceNewLeader({channel_name}): " + request.message)
        self.peer_service.reset_leader(request.new_leader_id, channel_name)
        return gbrick_pb2.CommonReply(response_code=define_code.Response.success, message="success")
