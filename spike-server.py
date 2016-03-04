#! /usr/bin/env python

import os
import logging
import argparse
from os.path import dirname, abspath
from shutil import move
from time import time, strftime, localtime

from spike import create_app, seeds, version
from spike.model import db, Settings, NaxsiRuleSets
from spike.model.naxsi_rules import ValueTemplates


def run():
    app = create_app(__get_config_file())

    try:
        app_port = int(app.config["APP_PORT"])
    except:
        app_port = 5555
    try:
        app_host = app.config["APP_HOST"]
    except:
        app_host = "127.0.0.1"

    db.init_app(app)
    app.test_request_context().push()

    try:
        eo_offset = Settings.query.filter(Settings.name == 'rules_offset').first()
        app.config["NAXSI_RULES_OFFSET"] = eo_offset.value
    except:
        app.config["NAXSI_RULES_OFFSET"] = 20000

    try:
        app.config["RULESET_HEADER"] = app.config["RULESET_HEADER"]
    except:
        app.config["RULESET_HEADER"] = ''

    logging.info("Spike is running on %s:%s", app_host, app_port)
    app.run(debug=True, host=app_host, port=app_port)


def spike_init():
    """ Import some data into Spkie internal DB, in order to be able to run it """
    it = ts = int(time())
    logging.info("Initializing Spike")

    ds = strftime("%F - %H:%M", localtime(time()))
    app = create_app(__get_config_file())

    db_files = app.config["SQLALCHEMY_BINDS"]

    for sqldb in db_files:
        p1 = os.path.join('spike', db_files[sqldb].replace("sqlite:///", ""))
        if os.path.isfile(p1):
            logging.info("Existing db found (%s) creating backup", sqldb)
            move(p1, os.path.join(p1, it))
            logging.info("copy: %s.%s", p1, it)

    app.test_request_context().push()
    db.init_app(app)

    with app.app_context():
        db.create_all()

    logging.info("filling default_vals")

    for v in seeds.vtemplate_seeds:
        logging.info("adding templates: %s" , v)
        for val in seeds.vtemplate_seeds[v]:
            db.session.add(ValueTemplates(v, val))

    for r in seeds.rulesets_seeds:
        logging.info("adding ruleset: %s / %s", r, seeds.rulesets_seeds[r])
        rmks = "naxsi-ruleset for %s / auto-created %s" % (r, ds)
        db.session.add(NaxsiRuleSets(seeds.rulesets_seeds[r], r, rmks, ts))

    for s in seeds.settings_seeds:
        logging.info("adding setting: %s", s)
        db.session.add(Settings(s, seeds.settings_seeds[s]))
    db.session.commit()

    logging.info('Spike initialization completed')


def __get_config_file():
    return os.path.join(dirname(abspath(__name__)), 'config.cfg')


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG, format='%(message)s')
    parser = argparse.ArgumentParser(description='Spike %s' % version)
    parser.add_argument('command', help='Run the spike server', choices=['run', 'init'])
    args = parser.parse_args()

    if args.command == 'run':
        run()
    elif args.command == 'init':
        spike_init()
