#!/usr/bin/python
# -*- coding:utf-8 -*-

import itertools
from pika import spec


class RabbitConsumerMessage(object):

    def __init__(
            self,routing_key,raw_body,
            parsed_body,method,props
    ):
        self.routing_key = routing_key
        self.raw_body = raw_body
        self.parsed_body = parsed_body
        self.method = method
        self.props = props

    def __str__(self):
        return str(self.__dict__)

#def call_middlewares(message,middlewares):
#    '''
#    call middlewares
#    :param message:
#    :param middlewares:[list]
#    :return:
#    '''
#    middlewares_iter = itertools.chain(middlewares,[lambda message,call_next])
#    def call_next(message):
#        try:
#            middleware = next(middlewares_iter)
#        except StopIteration as e:
#            raise e
#        middleware(message,call_next)
#
#    call_next(message)
