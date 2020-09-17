#!/usr/bin/env python
# encoding: utf-8

import lxml
import logging

from . import exception


def XMLGetAttribueByXPath(xml_elem, xpath):
    '''
    Get attribute by xpath for lxml element.
    The attribute specified by xpath must be unique, so in this function where is len == 1 check.
    The caller should catch the XMLParseException to handle parsing failed.
    '''
    if not isinstance(xml_elem, lxml.etree._Element):
        raise exception.XMLParseException("invalid xml_elem")

    attrib = xml_elem.xpath(xpath)
    if len(attrib) != 1:
        err_msg = 'failed to find attrib with xpath: %s' % (xpath)
        logging.error(err_msg)
        raise exception.XMLParseException(err_msg)

    return attrib[0]
