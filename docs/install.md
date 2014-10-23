

# Installation and Setup

## Requirements

- this should run on any decent linux-server with just some requirements, like

    - python 2.7 (not tested with 3.x, but fails with 2.6, esp. flask-bcrypt/sqlalchemy)
    - python-virtualenv
    - python-dev / headers
    - probably some build-essentials: gcc, make'n' stuff (for building flask/sqlalchemy)
    - sqlite3 


## Setup

- `git clone https://bitbucket.org/nginx-goodies/spike.git`
- edit spike/seeds.py and adjust settings_seeds {}, esp. when contributing to the community
- `cd spike && bash install.sh`
- edit config.cfg and adjust APP_PORT and APP_HOST (listen ip)
- run `./server run`
- have fun!



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
