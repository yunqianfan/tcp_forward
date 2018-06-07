
import logging

from common import connector
from common import forward_data
from common.cfg_manager import CfgManager
from common.data_handler import DataHandler
from common.protocol_handler import ProtocolHandler

logger = logging.getLogger('my_logger')

class OutDataHandler(DataHandler):
    """
    In this section,we must calculate an suitable package size according to the network bandwidth
    Suppose I want the network card to send a packet of data within one second,then the package size must smaller than the bandwidth
    So i calculated the approximate value by dividing the bandwidth by two
    """
    def __init__(self):
        self.__bandwidth = CfgManager.get_instance().get_cfg().get('DEFAULT','BANDWIDTH')
        self.__one_package_size = int(self.__bandwidth) * 1024 * 1024 / 8 / 2

    def create_connection(self,forward_id,inner_ip,inner_port,inner_connector):
        _protocol_handler = ProtocolHandler()
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.NEW_CONNECTION, forward_id,
                                             inner_ip, inner_port, '')
        send_package = _protocol_handler.build_data(forw_data)
        if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            send_bytes = inner_connector.send(send_package)
            if send_bytes <= 0:
                logger.error("CreateConnectionData send failed,forward_id:%d inner_ip:%s inner_port:%d" % (forward_id, inner_ip, inner_port))

    def trans_data(self,forward_id,inner_ip,inner_port,data,inner_connector):
        cfg = CfgManager.get_instance().get_cfg()
        ori = 0
        total_len = len(data)

        while ori < total_len:
            if total_len - ori <= self.__one_package_size:
                send_data = data[ori:total_len]
            else:
                send_data = data[ori:ori + self.__one_package_size]

            _protocol_handler = ProtocolHandler()
            forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.TRANS_DATA, forward_id,
                                                 inner_ip, inner_port, send_data)
            send_package = _protocol_handler.build_data(forw_data)
            if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
                send_bytes = inner_connector.send(send_package)
                if send_bytes <= 0:
                    logger.error("TransData to inner send failed,forward_id:%d inner_ip:%s inner_port:%d" % (forward_id, inner_ip, inner_port))
                    raise Exception("Send data failed")
                #print 'inner_connector send package'
                #tools.print_hex_buf(send_package)
            ori += self.__one_package_size


    def close_connection(self,forward_id,inner_ip,inner_port,inner_connector):
        _protocol_handler = ProtocolHandler()
        forw_data = forward_data.ForwardData(forward_data.DATA_TYPE.CLOSE_CONNECTION, forward_id,
                                             inner_ip, inner_port, '')
        send_package = _protocol_handler.build_data(forw_data)
        if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            send_bytes = inner_connector.send(send_package)
            if send_bytes <= 0:
                logger.error("CloseConnectionData send failed,forward_id:%d inner_ip:%s inner_port:%d" % (forward_id, inner_ip, inner_port))

class InnerDataHandler(DataHandler):

    def send_pre_working(self,inner_connector):
        _protocol_handler = ProtocolHandler()
        pre_work_data = forward_data.ForwardData(forward_data.DATA_TYPE.PRE_WORKING,0,'0.0.0.0',0,'')
        send_package = _protocol_handler.build_data(pre_work_data)
        if inner_connector and inner_connector.con_state == connector.CON_STATE.CON_CONNECTED:
            send_bytes = inner_connector.send(send_package)
            if send_bytes <= 0:
                logger.error("Preworking data send error")
                raise Exception("Send data failed")

    def handle_pre_working_response(self, ring_buffer):
        while True:
            parsed_data = super(InnerDataHandler, self).parse_data(ring_buffer)
            if parsed_data == None:
                return None

            if parsed_data.data_type == forward_data.DATA_TYPE.PRE_WORKING:
                tag = str(parsed_data.data)
                return tag

    def handle_data(self, ring_buffer,worker_manager):
        while True:
            parsed_data = super(InnerDataHandler, self).parse_data(ring_buffer)
            if parsed_data == None:
                return

            if parsed_data.data_type == forward_data.DATA_TYPE.CONNECTION_SUCCESS:
                outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
                if outer_worker != None:
                    outer_worker.connecting_reply(True)
            elif parsed_data.data_type == forward_data.DATA_TYPE.TRANS_DATA:
                outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
                if outer_worker != None and outer_worker.is_working():
                    outer_worker.trans_data(parsed_data.data)
            elif parsed_data.data_type == forward_data.DATA_TYPE.CLOSE_CONNECTION:
                outer_worker = worker_manager.get_worker_by_id(parsed_data.id)
                if outer_worker != None:
                    outer_worker.close()
            elif parsed_data.data_type == forward_data.DATA_TYPE.HEART_BEAT:
                logger.debug('Recv heartbeat')