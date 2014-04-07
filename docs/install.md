

# Installation and Setup

## Requirements

- python 2.7 (not tested with 3.x, but fails with 2.6, esp. flask-bcrypt/sqlalchemy)
- python-virtualenv
- python-dev / headers
- probably some build-essentials: gcc, make'n' stuff
- sqlite3 

- git clone https://bitbucket.org/nginx-goodies/spike.git
- cd spike && bash install.sh

## Setup

- OBSOLETE, is sseded now and configurable setting / edit config.cfg and adjust NAXSI_RULES_EXPORT to point to a dircetory where 
  your exported Naxsi-Rulesets should be stored; can be either a absolute or relative path

- run `./server init`

you should be ready now to start using Spike!



## Put Spike behind Nginx

- tbd
