#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import requests
import traceback


class Notifier(object):
    def __init__(self):
        pass

    def Notify(self):
        raise NotImplementedError('Method not implemented!')


class RestfulNotifier(Notifier):
    def __init__(self, uri):
        self.__uri = uri

    def Notify(self, context):
        try:
            requests.post(self.__uri, data=context)
        except requests.exceptions.RequestException:
            logging.error(traceback.format_exc())
            logging.error('failed to notify uri: %s, context %s' % (self.__uri,
                                                                    context))
