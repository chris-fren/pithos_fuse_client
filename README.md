# pithosfuse


### SYNOPSIS

    pithosfuse [options] [fuse options] <mount point>


### DESCRIPTION

pithosfuse is a file system in user space that let you browse your
Pithos+ files.

### Install

pithosfuse requires `fusepy` and `kamaki`. All requirements should be installed
automatically by `pip` or `distribute`.

With pip::

    $ pip install pithosfuse

or with distribute::

    $ python setup.py install


* fusepy: https://pypi.python.org/pypi/fusepy
* kamaki: https://pypi.python.org/pypi/kamaki
* FUSE: http://fuse.sourceforge.net/
* pip: http://pypi.python.org/pypi/pip
* distribute: http://pypi.python.org/pypi/distribute


### OPTIONS

-c CLOUD, --cloud=CLOUD         Use this kamaki 'cloud' instead of default

-u ACCOUNT, --url=ACCOUNT       Authentication URL

-t TOKEN, --token=TOKEN         Access Token

-d, --debug                     Turn on debug output (alomg with -f)

-s, --nothreads                 Disallow multi-threaded operation.
                                Run with only one thread

-f, --foreground                Run in foreground

-o EXTRA_OPTIONS, --options=EXTRA_OPTIONS
                                Comma seperated key=val options for FUSE

-m POOLSIZE, --max-poolsize=POOLSIZE
                                Max HTTP Pooled connections (default:8)
