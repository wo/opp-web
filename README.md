# opp-web

## Installation

First, we need the [opp-tools](http://github.com/wo/opp-tools) package. Then 

    cd opp-web
    sudo pip install virtualenv
    virtualenv venv
    . venv/bin/activate
    pip install Flask
    pip install flask-mysql

For production, I use mod_wsgi, set up as described in the [Flask manual](http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/). 




