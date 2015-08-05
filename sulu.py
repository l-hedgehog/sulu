#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this file,
# You can obtain one at http://mozilla.org/MPL/2.0/.
#

__version__ = '0.1.20150805'

import hashlib, os, sys
try:
    import rdflib
except ImportError:
    sys.exit('Requires rdflib')

em = rdflib.Namespace('http://www.mozilla.org/2004/em-rdf#')

def asn1_der(string):
    import binascii
    try:
        from pyasn1.codec.der import encoder as der_encoder
        from pyasn1.type.univ import BitString, Null, ObjectIdentifier, Sequence
    except ImportError:
        sys.exit('Requires pyasn1')

    sha512WithRSAEncryption = ObjectIdentifier('1.2.840.113549.1.1.13')
    algorithm = Sequence().setComponentByPosition(
        0,
        sha512WithRSAEncryption
    ).setComponentByPosition(
        1,
        Null('')
    )
    signature = Sequence().setComponentByPosition(
        0,
        algorithm
    ).setComponentByPosition(
        1,
        BitString("'%s'H" % binascii.hexlify(string))
    )

    return der_encoder.encode(signature)

def serialize_rdf(update_graph, signing):
    '''Tweak rdflib's pretty-xml serialization of update_graph into
    the "indentical" representation as defined in http://mzl.la/x4XF6o
    '''
    unsorted_s = update_graph.serialize(format = 'pretty-xml')
    unsorted_s = unsorted_s.replace('xmlns:rdf', 'xmlns:RDF')
    unsorted_s = unsorted_s.replace('rdf:', 'RDF:')
    unsorted_s = unsorted_s.replace('RDF:about', 'about')
    unsorted_s = unsorted_s.split('\n')
    start, end = unsorted_s[0:5], unsorted_s[-2:]
    unsorted_s = unsorted_s[5:-2]
    if signing:
        unsorted_s = [line[2:] for line in unsorted_s]
        unsorted_s.append('')
    sorting_s = []
    prev_leading_spaces = -2
    for line in unsorted_s:
        leading_spaces = len(line) - len(line.lstrip())
        if leading_spaces > prev_leading_spaces:
            sorting_s.append([line])
        elif leading_spaces == prev_leading_spaces:
            sorting_s[-1].append(line)
        elif leading_spaces < prev_leading_spaces:
            tmp_line = sorting_s.pop()
            tmp_line = '\n'.join(sorted(tmp_line))
            tmp_line = [sorting_s[-1].pop(), tmp_line, line]
            tmp_line = '\n'.join(tmp_line)
            sorting_s[-1].append(tmp_line)
        prev_leading_spaces = leading_spaces
    if signing:
        sorted_s = '\n'.join(sorting_s[0])
    else:
        sorted_s = []
        sorted_s.extend(start)
        sorted_s.extend(sorting_s[0])
        sorted_s.extend(end)
        sorted_s = '\n'.join(sorted_s)
    return sorted_s

def get_signature(update_graph, key_file, get_pass_phrase):
    import base64
    private_key = get_privatekey(key_file, get_pass_phrase)

    return base64.b64encode(
        asn1_der(
            private_key.sign(
                hashlib.sha512(
                    serialize_rdf(update_graph, True)
                ).digest(),
                'sha512'
            )
        )
    ).replace('\n', '')

def get_privatekey(key_file, get_pass_phrase):
    try:
        from M2Crypto import RSA
    except ImportError:
        sys.exit('Requires M2Crypto & OpenSSL')

    try:
        private_key = RSA.load_key(key_file, get_pass_phrase)
    except RSA.RSAError:
        sys.exit('Bad private key or incorrect passphrase')

    return private_key

def get_pubkey(key_file, get_pass_phrase):
    try:
        from M2Crypto import RSA
    except ImportError:
        sys.exit('Requires M2Crypto & OpenSSL')

    private_key = get_privatekey(key_file, get_pass_phrase)

    return RSA.new_pub_key(
        private_key.pub()
    ).as_pem()

def get_xpi_hash(xpi_file):
    xpi = open(xpi_file, 'rb')
    xpi_string = xpi.read()
    xpi.close()

    return '%s:%s' % ('sha256', hashlib.sha256(xpi_string).hexdigest())

def get_install_string(xpi_file):
    import zipfile

    xpi = zipfile.ZipFile(xpi_file)
    install_string = xpi.read('install.rdf')
    xpi.close()
    return install_string

def get_install_info(xpi_file, update_link, get_max_version):
    try:
        from lxml import etree
    except ImportError:
        sys.exit('Requires lxml')

    install_tree = etree.fromstring(get_install_string(xpi_file))
    nsmap = {
        'em': 'http://www.mozilla.org/2004/em-rdf#',
        'RDF': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    }
    triples = [];

    description = install_tree.find('RDF:Description', nsmap)
    install_id = description.findtext('em:id', None, nsmap)
    update_url = description.findtext('em:updateURL', None, nsmap)
    if update_url:
        if not update_url.startswith('https://'):
            if not description.findtext('em:updateKey', None, nsmap):
                raise UserWarning('No em:updateKey in install.rdf')
    if update_link == '.':
        if not update_url:
            sys.exit('No em:updateURL in install.rdf')
        update_link = '/'.join([
            os.path.dirname(update_url),
            os.path.basename(xpi_file)
        ])
    update_hash = get_xpi_hash(xpi_file)
    ext_ver = description.findtext('em:version', None, nsmap)
    version = rdflib.BNode('updates:%s' % ext_ver)
    triples.append((version, em['version'], rdflib.Literal(ext_ver)))

    target_applications = description.findall('em:targetApplication', nsmap)
    for target_application in target_applications:
        target_application = target_application.find('RDF:Description', nsmap)
        tmp = {}
        for key in ['id', 'minVersion', 'maxVersion']:
            tmp[key] = target_application.findtext('em:%s' % key, None, nsmap)
        if get_max_version:
            tmp['maxVersion'] = get_max_version(tmp['id']) or tmp['maxVersion']
        tarapp = rdflib.BNode('updates:%s:%s' % (ext_ver, tmp['id']))
        for key in ['id', 'minVersion', 'maxVersion']:
            triples.append((tarapp, em[key], rdflib.Literal(tmp[key])))
        triples.append((tarapp, em['updateLink'], rdflib.Literal(update_link)))
        triples.append((tarapp, em['updateHash'], rdflib.Literal(update_hash)))
        triples.append((version, em['targetApplication'], tarapp))

    return (install_id, version, triples)

def get_update_info(input_infos):
    update_triples = []
    update = None
    updates = rdflib.BNode('updates')
    update_triples.append((updates, rdflib.RDF['type'], rdflib.RDF['Seq']))
    for xpi_file, update_link, get_max_version in input_infos:
        install_id, version, install_triples = get_install_info(
            xpi_file,
            update_link,
            get_max_version
        )
        install_id = rdflib.term.URIRef('urn:mozilla:extension:%s' % install_id)
        if update and update != install_id:
            sys.exit('multiple xpis should have same id')
        update = install_id
        update_triples.extend(install_triples)
        update_triples.append((updates, rdflib.RDF['li'], version))
    update_triples.append((update, em['updates'], updates))
    return update, update_triples

def sign_update_rdf(input_infos, key_file, output_file, get_pass_phrase):
    try:
        ext_id, update_triples = get_update_info(input_infos)
    except UserWarning, msg:
        pubkey = get_pubkey(key_file, get_pass_phrase)
        print '%s\n%s' % (msg, pubkey)
        return 0

    update_graph = rdflib.Graph()
    update_graph.bind('em', em)
    for t in update_triples:
        update_graph.add(t)
    update_graph.commit()

    signature = get_signature(update_graph, key_file, get_pass_phrase)
    update_graph.add((ext_id, em['signature'], rdflib.Literal(signature)))
    update_graph.commit()

    if output_file == '-':
        dest = sys.stdout
    else:
        dest = open(output_file, 'w')
    dest.write(serialize_rdf(update_graph, False))
    dest.close()
    return 0

def pass_phrase_cb(pass_phrase_opt):
    def get_passphrase(v):
        from getpass import getpass
        return {
            '-': lambda x : getpass('Passphrase for the private key: '),
            '=': lambda x : x,
            '@': lambda x : open(x).readline().rstrip(),
            '$': lambda x : os.getenv(x),
            '&': lambda x : os.fdopen(int(x)).readline().rstrip(),
        }[pass_phrase_opt[0]](pass_phrase_opt[1:])

    return get_passphrase

def max_version_cb(max_version_file):
    if not max_version_file:
        return None

    version_overrides_info = {}
    max_version = open(max_version_file)
    app_id_versions = max_version.readlines()
    max_version.close()
    for app_id_version in app_id_versions:
        app_id, app_version = app_id_version.split()
        version_overrides_info[app_id] = app_version

    def max_version_for_app(app_id):
        if app_id in version_overrides_info:
            return version_overrides_info[app_id]
        else:
            return ''

    return max_version_for_app

def parse_opts():
    import optparse

    kw = {
        'version' : __version__,
        'usage' : '%prog [options] ext.xpi update_link [override.txt] ...',
        'conflict_handler' : 'resolve',
    }
    parser = optparse.OptionParser(**kw)

    parser.add_option('-h', '--help',
        action='help',
        help='print this help text and exit')
    parser.add_option('-v', '--version',
        action='version',
        help='print program version and exit')
    parser.add_option('-k',
        dest='key_file', metavar='KEYFILE',
        help='private key (*.pem) used to sign the update.rdf')
    parser.add_option('-p',
        dest='pass_phrase', metavar='PASSPHRASE',
        help='passphrase for the key, supports \'-=@$&\' syntax of uhura',
        default='-')
    parser.add_option('-o',
        dest='output_file', metavar='OUTFILE',
        help='the path to the output update.rdf, use \'-\' for stdout',
        default='-')
    parser.add_option('-m',
        action='store_true', dest='max_version',
        help='use maxVersion in override.txt instead of install.rdf',
        default=False)

    opts, args = parser.parse_args()
    return parser, opts, args

def main():
    parser, opts, args = parse_opts()
    if '-=@$&'.find(opts.pass_phrase[0]) < 0:
        parser.error('unkown passphrase option: %s' % opts.pass_phrase)

    expect_argc = 2
    if opts.max_version:
        expect_argc += 1
    if (not args) or (len(args) % expect_argc):
        error_msg = ['ext.xpi and update_link should be provided']
        if opts.max_version:
            error_msg.append('also the txt with override information')
        parser.error('\n'.join(error_msg))

    input_infos = []
    while args:
        xpi_file    = args.pop(0)
        update_link = args.pop(0)
        override    = args.pop(0) if opts.max_version else ''
        input_infos.append([xpi_file, update_link, max_version_cb(override)])

    get_passphrase = pass_phrase_cb(opts.pass_phrase)

    retcode = sign_update_rdf(
        input_infos,
        opts.key_file,
        opts.output_file,
        get_passphrase
    )
    sys.exit(retcode)

if __name__ == '__main__':
    main()
