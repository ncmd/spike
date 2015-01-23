

## Spike Installation and Setup


### WARNING

> 
> Spike ist still very early alpha.
>
> NEVER run Spike! on a public facing Server; there's absolutely 
> no protection or user-login atm; exposing Spike! to the public could
> lead into damaged or deleted rules 
>
> Really
>
>



### Requirements

- this should run on any decent linux-server with just some requirements, like

    - python 2.7 (not tested with 3.x, might fail with 2.6, esp. flask-bcrypt/sqlalchemy)
    - python-virtualenv
    - python-dev / headers
    - probably some build-essentials: gcc, make'n' stuff (for building flask/sqlalchemy)
    - sqlite3 


### Setup

- [Spike - Repo @ Bitbucket](https://bitbucket.org/nginx-goodies/spike/overview)

- `git clone https://bitbucket.org/nginx-goodies/spike.git`
- edit spike/seeds.py and adjust settings_seeds {}, esp. 'rules_offset' when contributing to the community
- `cd spike && bash install.sh`
- edit config.cfg and adjust APP_PORT and APP_HOST (listen ip)
- run `./server run`
- have fun!



### Config

- most config-options are accessible through the webinterface via http://spike.local:5555/settings/, except:
    - APP_PORT -> the port the spike-server listens on (defaults to 5555)
    - APP_HOST -> the ip to bind to (defaults to 127.0.0.1)
    - RULESET_HEADER -> the header that get written to each ruleset.rules; you might use some placeholders:
        - RULESET_DESC -> value from DESC
        - RULESET_FILE -> ruleset_filename
        - RULESET_DATE -> export-date




### Put Spike behind Nginx

~~~

# spike.conf

  server {

    server_tokens off;

    #listen 443 ssl;
    listen 80;
    server_name spike.nginx-goodies.com  ;

    proxy_cache             off;
    gzip on;
    expires off;
    keepalive_timeout 5;


    proxy_set_header    X-Forwarded-For   $proxy_add_x_forwarded_for;
    proxy_set_header    X-Real-IP         $remote_addr;
    proxy_set_header    Host              $host;
    proxy_set_header    X-Forwarded-Proto $scheme;


    access_log  /var/log/nginx/spike.access.log; 
    error_log  /var/log/nginx/error.log;

    add_header X-Frame-Options SAMEORIGIN;
    add_header Access-Control-Allow-Origin "$scheme://$http_host";

    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";

    add_header Cache-Control public;        

    root /srv/data/www/spike/spike;


    # path for static files
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

# spike-wl.rules

BasicRule wl:1100 "mz:$BODY_VAR:rmks";
BasicRule wl:1101 "mz:$BODY_VAR:rmks";


~~~
