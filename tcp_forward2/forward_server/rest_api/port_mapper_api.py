import api
import info_collection

class PortMapperApi(api.RestApiHandler):

    def _get(self,request):
        return self.__get_request()

    def _post(self,request):
        #create new port mapper

        params = self._get_params(request)
        if not params.has_key('port') or \
            not params.has_key('mapper_ip') or \
            not params.has_key('mapper_port') or \
            not params.has_key('mapper_tag'):
            return [str({'result':'failed','reason':'parms error'})]

        try:


            info_collection.InfoCollection.get_instance().create_new_port(int(params['port']),
                                                                      params['mapper_ip'],
                                                                      int(params['mapper_port']),
                                                                      params['mapper_tag'])
        except Exception,e:
            return [str({'result': 'failed', 'reason': e.message})]
        return [str({'result': 'success'})]

    def _delete(self,request):
        #delete port mapper

        params = self._get_params(request)

        if not params.has_key('port'):
            return [str({'result': 'failed', 'reason': 'parms error'})]

        try:
            info_collection.InfoCollection.get_instance().delete_port(int(params['port']))
        except Exception,e:
            return [str({'result': 'failed', 'reason': e.message})]
        return [str({'result': 'success'})]

    def __get_request(self):
        collection = info_collection.InfoCollection.get_instance()
        return [collection.get_port_mapper_str()]


    @classmethod
    def factory(cls,global_conf,**kwargs):
        return cls()
