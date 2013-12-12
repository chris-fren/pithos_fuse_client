==========
pithosfuse
==========

------------------------------------------------------------
File system ins user space using FUSE_ and `Kamaki client`_.
------------------------------------------------------------

:Author: cnanakos
:Date: 2013-12-12
:Copyright: Lesser GNU Public License
:Version: 0.1
:Manual section: 1
:Manual group: FUSE


SYNOPSIS
========
    pithosfuse [options] [fuse options] <mount point>


DESCRIPTION
===========

|pithosfuse| is a file system in user space that let you browse your
|Pithos+| files.

Install
-------

|pithosfuse| requires fusepy_ and kamaki_. All requirements should be installed
automatically by pip_ or distribute_.

With pip::

    $ pip install pithosfuse

or with distribute::

    $ python setup.py install

.. |pithosfuse| replace:: pithosfuse
.. |Pithos+| replace:: Pithos+

.. _fusepy: https://pypi.python.org/pypi/fusepy
.. _kamaki: https://pypi.python.org/pypi/kamaki
.. _FUSE: http://fuse.sourceforge.net/
.. _`pip`: http://pypi.python.org/pypi/pip
.. _`distribute`: http://pypi.python.org/pypi/distribute


OPTIONS
=======

Common Options:
  -c CLOUD, --cloud=CLOUD
                      Use this kamaki 'cloud' instead of default
  -u ACCOUNT, --url=ACCOUNT
                      Authentication URL
  -t TOKEN, --token=TOKEN
                      Access Token

Debug Options:
  -d, --debug         Turn on debug output (alomg with -f)
  -s, --nothreads     Disallow multi-threaded operation. Run with only one
                        thread
  -f, --foreground    Run in foreground

Extra options:
  -o EXTRA_OPTIONS, --options=EXTRA_OPTIONS
                      Comma seperated key=val options for FUSE
