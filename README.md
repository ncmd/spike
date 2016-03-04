# Spike! - Naxsi Rules Builder

[![Code Health](https://landscape.io/github/nbs-system/spike/master/landscape.svg?style=flat)](https://landscape.io/github/nbs-system/spike/master)
[![Codacy Badge](https://api.codacy.com/project/badge/grade/f16a87616f3c4e14ac914fea520298e7)](https://www.codacy.com/app/julien-voisin/spike)
[![Scrutinizer Code Quality](https://scrutinizer-ci.com/g/nbs-system/spike/badges/quality-score.png?b=master)](https://scrutinizer-ci.com/g/nbs-system/spike/?branch=master)

Spike is a simple web application to manage [naxsi]( https://github.com/nbs-system/naxsi ) rules.
Rules are stored in a [sqlite]( https://www.sqlite.org/ ) database, and can be added,
deleted, modified, searched, importable and exportable in plain-text.

This software was initially created to help with keeping the [Doxi]( https://bitbucket.org/lazy_dogtown/doxi-rules/src )
rulesets up-to-date. It was created with love by the people of [mare system]( https://www.mare-system.de/ ) in 2011,
maintained by [8ack]( https://8ack.de/corporate ), and now, it's being adopted by the naxsi project.

It's proudly powered by [flask]( http://flask.pocoo.org/ ) and [sqlalchemy]( http://www.sqlalchemy.org/ ).

You can take a look [here]( http://spike.nginx-goodies.com/rules/ ) for a  live (legacy) version.

# WARNING

> 
> Spike ist still very early alpha.
>
> NEVER run Spike! on a public facing Server; there's absolutely 
> no protection or user-login atm; exposing Spike! to the public could
> lead into damaged or deleted rules 
>
> Really


# Spike Installation and Setup

## Requirements

To run, spike needs:

- python2.7
- python-sqlite
- sqlalchemy
- flask
- flask-bootstrap
- flask-sqlalchemy


### Setup

```bash
git clone https://github.com/spike
pip install flask
pip install flask-bootstrap
pip install flask-sqlalchemy
pip install flask-wtf
pip install markdown
python ./spike-server.py run
```

### Configuration

Check the config.cfg file:

- APP_PORT -> the port the spike-server listens on (defaults to 5555)
- APP_HOST -> the ip to bind to (defaults to 127.0.0.1)
- RULESET_HEADER -> the header that get written to each ruleset.rules; you might use some placeholders:
    - RULESET_DESC -> value from DESC
    - RULESET_FILE -> ruleset_filename
    - RULESET_DATE -> export-date


### Putting Spike behind Nginx

    
    server {
        server_tokens off;
        listen 443 ssl;
        server_name spike.nginx-goodies.com  ;
        
        proxy_set_header    X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header    X-Real-IP         $remote_addr;
        proxy_set_header    Host              $host;
        proxy_set_header    X-Forwarded-Proto $scheme;
        
        access_log  /var/log/nginx/spike.access.log; 
        error_log  /var/log/nginx/error.log;
        
        root /var//www/spike;
        
        location  /static {
            autoindex off;
            expires 1d;
        }
        
        location / {
            proxy_cache off;
            proxy_redirect off;
            proxy_pass http://127.0.0.1:5555;
            expires off;
            include /etc/nginx/doxi-rules/active-mode.rules;
            include /etc/nginx/doxi-rules/local.rules;
            include /etc/nginx/doxi-rules/spike-wl.rules;
        }
    }
    
    # spike-wl.rules for naxsi (you're running naxsi on your nginx setup, right ?)
    
    BasicRule wl:1100 "mz:$BODY_VAR:rmks";
    BasicRule wl:1101 "mz:$BODY_VAR:rmks";


# Screenshots

![Rules creation]( https://raw.githubusercontent.com/nbs-system/spike/master/docs/rule_creation.png )
![Rules set management]( https://raw.githubusercontent.com/nbs-system/spike/master/docs/rulesets.png )


# Links

- [Naxsi]( https://github.com/nbs-system/naxsi )
- [Doxi-Rules]( https://bitbucket.org/lazy_dogtown/doxi-rules/src )
- [Naxsi wiki]( https://github.com/nbs-system/naxsi/wiki )
