import sys
import argparse

import consul_kv_xml


def main(args):
    parser = argparse.ArgumentParser(
        prog='consul_kv_xml',
        description="Ser/des of XML documents for Hashicorp's Consul KV store")
    parser.add_argument(
        '--http',
        metavar='host:port',
        default='localhost:8500',
        help='Consul HTTP REST API endpoint')
    subparsers = parser.add_subparsers(
        description='operation modes (try consul_kv_xml read -h etc.)')

    read_parser = subparsers.add_parser(
        'read', help='Read from Consul KV and format the data as XML')
    read_parser.add_argument(
        '-k',
        '--key',
        metavar='k/e/y',
        help='key to query the Consul KV store')
    read_parser.add_argument(
        '-f',
        '--file',
        metavar='out.xml',
        default='-',
        help='output file (default: stdout)')
    read_parser.set_defaults(func=consul_kv_xml.do_read)

    write_parser = subparsers.add_parser(
        'write', help='Write the input XML data into Consul KV')
    write_parser.add_argument(
        '-k',
        '--key',
        metavar='k/e/y',
        help='key to write to the Consul KV store')
    write_parser.add_argument(
        '-f',
        '--file',
        metavar='in.xml',
        default='-',
        help='input file (default: stdin)')
    write_parser.set_defaults(func=consul_kv_xml.do_write)

    opts = parser.parse_args()
    opts.func(opts)


main(sys.argv[1:])
