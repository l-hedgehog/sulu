#!/usr/bin/env python
import os
import rdflib
import sulu
import unittest

class TestSerializeRdf(unittest.TestCase):
    def setUp(self):
        self.update_graph = rdflib.Graph().parse('test/update.rdf')
        self.signing_rdf  = open('test/signing.txt').read()
        self.complete_rdf = open('test/complete.txt').read()

    def test_signing(self):
        self.assertEqual(sulu.serialize_rdf(self.update_graph, True), self.signing_rdf)

    def test_complete(self):
        self.assertEqual(sulu.serialize_rdf(self.update_graph, False), self.complete_rdf)

class TestPassPhraseCb(unittest.TestCase):
    def setUp(self):
        self.pp_file      = 'test/pass_phrase'
        self.pass_phrase  = open(self.pp_file).readline().rstrip()
        self.pp_env       = 'PASS_PHRASE'

        os.environ[self.pp_env] = self.pass_phrase

    def test_direct(self):
        self.assertEqual(sulu.pass_phrase_cb('=%s' % self.pass_phrase)(0), self.pass_phrase)

    def test_file(self):
        self.assertEqual(sulu.pass_phrase_cb('@%s' % self.pp_file)(0), self.pass_phrase)

    def test_env(self):
        self.assertEqual(sulu.pass_phrase_cb('$%s' % self.pp_env)(0), self.pass_phrase)

    def test_fd(self):
        fd = os.open(self.pp_file, os.O_RDONLY)
        self.assertEqual(sulu.pass_phrase_cb('&%s' % fd)(0), self.pass_phrase)

class TestMaxVersionCb(unittest.TestCase):
    def setUp(self):
        self.firefox      = '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}'
        self.thunderbird  = '{3550f703-e582-4d05-9a08-453d09bdfdc6}'
        self.override     = 'docs/override.txt-sample'
        self.firefox_ver  = '13.*'

    def test_firefox(self):
        self.assertEqual(sulu.max_version_cb(self.override)(self.firefox), self.firefox_ver)

    def test_thunderbird(self):
        self.assertEqual(sulu.max_version_cb(self.override)(self.thunderbird), '')

    def test_none(self):
        self.assertIsNone(sulu.max_version_cb(''))

if __name__ == '__main__':
    unittest.main()
