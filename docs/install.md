

# Installation and Setup

## Requirements

- python 2.7 (not tested with 3.x, but fails with 2.6, esp. flask-bcrypt/sqlalchemy)
- python-virtualenv
- python-dev / headers
- probably some build-essentials: gcc, make'n' stuff
- sqlite3 

- git clone https://bitbucket.org/nginx-goodies/spike.git
- cd spike && bash install.sh
- edit config.cfg and adjust accordingly 
- edit spike/seeds.py and adjust settings_seeds {}, esp. when contributing to
  the community

## Setup

- OBSOLETE, is seeded now and configurable setting / edit config.cfg and adjust NAXSI_RULES_EXPORT to point to a dircetory where 
  your exported Naxsi-Rulesets should be stored; can be either a absolute or relative path

- run `./server init`

you should be ready now to start using Spike!

## Config

- most config-options are accessible through the webinterface via http://spike.local:5555/settings/, except:
    - APP_PORT -> the port the spike-server listens on (defaults to 5555)
    - APP_HOST -> the ip to bind to (defaults to 127.0.0.1)
    - RULESET_HEADER -> the header that get written to each ruleset.rules; you might use some placeholders:
        - RULESET_DESC -> value from DESC
        - RULESET_FILE -> ruleset_filename
        - RULESET_DATE -> export-date



## Put Spike behind Nginx

- tbd
