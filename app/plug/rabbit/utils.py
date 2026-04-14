#!/usr/bin/python
# -*- coding:utf-8 -*-

'''use for rabbitmq'''


from enum import Enum

class ExchangeType(Enum):
    '''exchange type'''
    DIRECT = 'direct'
    FANOUT = 'fanout'
    TOPIC = 'topic'
    HEADERS = 'headers'


class QueueType(Enum):
    '''queue type'''
    CLASSIC = 'classic'
    QUORUM = 'quorum'
    LAZY = 'lazy'

class AMQPError(Exception):

    def __repr__(self):
        return '%s: An unspecified AMQP error has occurred; %s' % (
            self.__class__.__name__, self.args)


class AMQPConnectionError(AMQPError):

    def __repr__(self):
        if len(self.args) == 2:
            return '{}: ({}) {}'.format(self.__class__.__name__, self.args[0],
                                        self.args[1])
        else:
            return '{}: {}'.format(self.__class__.__name__, self.args)