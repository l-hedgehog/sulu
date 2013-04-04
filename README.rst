sulu
====

.. image:: https://travis-ci.org/l-hedgehog/sulu.png?branch=master
        :target: https://travis-ci.org/l-hedgehog/sulu

sulu is another tool for signing update.rdf of mozilla add-ons. It
is a drop-in replacement for uhura_ if you just want to generate a
signed update.rdf according to a xpi package and an update url.

Currently the options m/k/p/o are supported, h/v have different but
more common meanings. Other uhura features are not supported,
hopefully a Python implementation means more people will be able to
hack it.

The name sulu is choosed as McCoy, spock and uhura already existed
and the original author lives in East Asia :-)

.. _uhura: http://www.softlights.net/projects/mxtools/uhura.html
