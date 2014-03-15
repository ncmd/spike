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
pip install flask
pip install flask-login
pip install flask-bootstrap
pip install flask-sqlalchemy
pip install flask-bcrypt
pip install flask-wtf
pip install --upgrade simplejson
pip install --upgrade sqlite3 
#pip install redis
#pip install psycopg2
pip install markdown

echo ">  configuring" 

cp config.cfg.example config.cfg


echo "
> Install OK && DONE
>
> init your app now:
>  - edit config.cfg
>  - run ./spike-server init 
>  - start engines: ./spike-server run
> 
> have fun!
>
"



