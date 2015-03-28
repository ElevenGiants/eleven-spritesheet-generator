#!/usr/bin/env python
"""
Usage:
  worker.py [--config=<configfile>]

Options:
  -c --config=<configfile> The module to load for config. When not given,
    config.py in the current directory is tried, followed by
    eleven.worker.config. When given, only the given file is tried.

"""
import os
import sys

from docopt import docopt

from eleven.worker import SpritesheetGenerator


class Config(object):
    pass


def load_config(filename):
    vals = {}
    execfile(filename, vals, vals)
    config = Config()
    for key, val in vals.iteritems():
        setattr(config, key, val)
    return config


def main():
    args = docopt(__doc__)
    print args
    if args['--config'] is None:
        if os.path.exists('config.py'):
            config = load_config('config.py')
        else:
            from eleven.worker import default_config as config
    else:
        if not os.path.exists(args['--config']):
            print >>sys.stderr, 'Config file %r does not exist' % (args['--config'],)
            print >>sys.stderr, __doc__
        config = load_config(args['--config'])

    SpritesheetGenerator(
        config.asset_host_port,
        config.asset_url,
        config.api_url,
        config.secret_key,
        config.task_timeout,
        config.amqp_url,
        config.http_port
    ).run()


if __name__ == '__main__':
    main()
