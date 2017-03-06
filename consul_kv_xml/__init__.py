'''
Ser/des of XML documents for Hashicorp's Consul KV store
'''

import sys
import re
import os.path
import pprint
import xml.etree.ElementTree as ET
import xml.sax
import xml.sax.handler

import consul


def connect(http_endpoint):
    try:
        m = re.match(r'^(\S*?)(:\d+)?$', http_endpoint)
        host = m.group(1)
        port = int(m.group(2)[1:])
    except Exception as ex:
        raise Exception(
            "invalid endpoint {0!r}: {1}".format(http_endpoint, ex))

    return consul.Consul(host=host, port=port)


ALL_NUM = re.compile(r'^(\d+)(.*)$')


def rec_set_dic(d, v, kseq, i=0):
    k = kseq[i]
    if i + 1 == len(kseq):
        d[k] = v
    else:
        k = kseq[i]
        child = d.get(k)
        if None is child:
            child = {}
            d[k] = child
        rec_set_dic(child, v, kseq, i + 1)


def do_read(opts):
    consul = connect(opts.http)

    tree = {}

    for v in sorted(consul.kv.get(opts.key, recurse=True)[1], key=lambda e: e['Key']):
        kseq = os.path.relpath(v['Key'], opts.key).split('/')
        rec_set_dic(tree, v['Value'], kseq)

    pprint.PrettyPrinter().pprint(tree)

    def rec_set(xml, v, kseq, i=0):
        if i + 1 == len(kseq):
            if '@' == k0[0:1]:
                xml.set(k0[1:], v)
            else:
                m = ALL_NUM.match(k0)
                if m.group(2):
                    d1 = ET.SubElement(xml, m.group(2))
                    d1.text = v
        else:
            k = kseq[i]
            child = d.get(k0)
            if None is child:
                child = {}
                d[k0] = child
            rec_set(child, v, kseq, i + 1)

    xml = ET.ElementTree()
    rec_set(xml.getroot())
#   xml.write(opts.file or sys.stdout)


def do_write(opts):

    consul = connect(opts.http)

    def put(k, v):
        consul.kv.put(opts.key + k, v.encode('utf-8'))

    class Handler(xml.sax.handler.ContentHandler):
        def __init__(self):
            self._stack = [['', 0, False]]
            self._chars = []

        def startElement(self, name, attrs):
            name = "{0:04}".format(self._stack[-1][1]) + name
            self._stack[-1][2] = True
            if self._chars:
                self.commit_text()
            self._stack.append([name, 0, False])
            path = '/'.join(n for n, _, _ in self._stack)
            for k, v in attrs.items():
                put("{0}/@{1}".format(path, k), v)

        def characters(self, content):
            content = content.strip()
            if content:
                self._chars.append(content)

        def commit_text(self):
            path = '/'.join(n for n, _, _ in self._stack)
            if self._stack[-1][2]:
                path += "/{0:04}".format(self._stack[-1][1])
            put(path, ''.join(self._chars))
            del self._chars[:]
            self._stack[-1][1] += 1

        def endElement(self, name):
            if self._chars:
                self.commit_text()
            self._stack.pop()
            self._stack[-1][1] += 1

    p = xml.sax.make_parser()
    p.setContentHandler(Handler())
    # don't access the internet for DTD
    p.setFeature(xml.sax.handler.feature_external_ges, False)
    p.parse(opts.file or sys.stdin)
