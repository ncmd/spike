#! /usr/bin/env python

import os
import logging
import argparse
from os.path import dirname, abspath
import sys
from time import time, strftime, localtime

from spike import create_app, version
from spike.model import db, rulesets_seeds
from spike.model.naxsi_rulesets import NaxsiRuleSets


def run(debug=False):
    app = create_app(__get_config_file())
    db.init_app(app)
    app.test_request_context().push()

    try:
        host = app.config["APP_HOST"]
    except:
        host = '127.0.0.1'

    try:
        port = int(app.config["APP_HPOST"])
    except:
        port = 5555

    app.run(debug=debug, host=host, port=port)


def spike_init():
    logging.info("Initializing Spike")
    timestamp = int(time())

    app = create_app(__get_config_file())

    app.test_request_context().push()
    db.init_app(app)

    with app.app_context():
        db.create_all()

    logging.info("Filling default_vals")

    for r in rulesets_seeds:
        logging.info("Adding ruleset: %s", r)
        rmks = "Ruleset for %s / auto-created %s" % (r, strftime("%F - %H:%M", localtime(time())))
        db.session.add(NaxsiRuleSets(r, rmks, timestamp))

    db.session.commit()
    logging.info('Spike initialization completed')


def __get_config_file():
    return os.path.join(dirname(abspath(__name__)), 'config.cfg')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    parser = argparse.ArgumentParser(description='Spike %s' % version)
    parser.add_argument('command', help='Run the spike server', choices=['run', 'init'])
    parser.add_argument('-d', '--debug', help='Run server in debug mode', action='store_true')
    args = parser.parse_args()

    if args.command == 'run':
        if not os.path.exists(os.path.join(dirname(abspath(__name__)), 'spike', 'rules.db')):
            print('You should run `python %s init` before using Spike' % sys.argv[0])
        else:
            run(args.debug)
    elif args.command == 'init':
        spike_init()
