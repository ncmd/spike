# Spike! - Naxsi Rules Builder
[![Build Status](https://travis-ci.org/ncmd/spike.svg?branch=master)](https://travis-ci.org/ncmd/spike)

Spike is a simple web application to manage [naxsi]( https://github.com/nbs-system/naxsi ) rules.
Rules are stored in a [sqlite]( https://www.sqlite.org/ ) database, and can be added,
deleted, modified, searched, importable and exportable in plain-text.

This software was initially created to help with keeping the [Doxi]( https://bitbucket.org/lazy_dogtown/doxi-rules/src )
rulesets up-to-date. It was created with love by the people of [mare system]( https://www.mare-system.de/ ) in 2011,
maintained by [8ack]( https://8ack.de/corporate ), and now, it's being adopted by the naxsi project.

It runs on modern version of Python, and is proudly powered by
 [flask]( http://flask.pocoo.org/ ) and [sqlalchemy]( http://www.sqlalchemy.org/ ).

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

- `python`
- `python-sqlite`
- `sqlalchemy`
- `markdown`
- `flask`
- `flask-bootstrap`
- `flask-sqlalchemy`

You can also install the following optional dependencies:

- `python-pcre` for regexp validation

### Setup

```bash
git clone https://github.com/ncmd/spike
pip install virtualenv
cd spike
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python ./spike-server.py init
python ./spike-server.py run

Visit http://127.0.0.1:5555
To exit virtual environment:
deactivate
```

### Configuration

Check the config.cfg file:

- **APP_PORT**: the port the spike-server listens on (defaults to 5555)
- **APP_HOST**: the ip to bind to (defaults to 127.0.0.1)
- **RULESET_HEADER**: the header that get written to each ruleset.rules; you might use some placeholders:
- **RULESET_DESC**: value from DESC
- **RULESET_FILE**: ruleset_filename
- **RULESET_DATE**: export-date


### Putting Spike behind Nginx

    
    server {
        server_tokens off;
        listen 443 ssl;
        server_name spike.securethebox.us  ;
        
        proxy_set_header    X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header    X-Real-IP         $remote_addr;
        proxy_set_header    Host              $host;
        proxy_set_header    X-Forwarded-Proto $scheme;
        
        access_log  /var/log/nginx/spike.access.log; 
        error_log  /var/log/nginx/error.log;
        
        root /var/www/spike;
        
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
