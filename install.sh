#!/bin/bash
#
#
vdir="venv" 


echo "

SPIKE - APP_INSTALL

"
echo "[i] Initializing " 

if [ -d "$vdir" ]; then
echo "  >  old venv found, creating new" 
    rm -Rf $vdir
fi
echo "  >  installing new virtual-env in $vdir" 

echo ">  installing virtualenv in $vdir" 
virtualenv $vdir

. $vdir/bin/activate

echo ">  installing flask" 
pip install --upgrade flask
pip install --upgrade  flask-login
pip install --upgrade  flask-bootstrap
pip install --upgrade  flask-sqlalchemy
pip install --upgrade  flask-bcrypt
pip install --upgrade  flask-wtf
pip install --upgrade simplejson
pip install --upgrade sqlite3 
#pip install redis
#pip install psycopg2
pip install --upgrade  markdown

echo ">  configuring" 

cp config.cfg.example config.cfg


echo "
> Install OK && DONE
>
> init your app now:
>  - edit config.cfg
>  - run ./server init 
>  - start engines: ./server run
> 
> have fun!
>
"



