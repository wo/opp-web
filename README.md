# opp-web

## Installation

1. Install the [opp-tools](http://github.com/wo/opp-tools) package.

2. Then add a line to opp-tools/config.pl saying

    OPP_WEB => 1,

3. Install [scikit-learn](http://scikit-learn.org/stable/install.html).

4. Set up and edit the config file:

    cd opp-web
    mv config-default.py config.py
    vim config.py

5. Set up the database tables:

    mysql -u dbuser -p dbname < setup.sql 

6. For the frontend:

    sudo pip install virtualenv
    virtualenv venv
    . venv/bin/activate
    pip install Flask
    pip install flask-mysql

For production, I use mod_wsgi, set up as described in the [Flask manual](http://flask.pocoo.org/docs/0.10/deploying/mod_wsgi/), 
except for [this tweak to make it play with scipy](http://serverfault.com/questions/514242/non-responsive-apache-mod-wsgi-after-installing-scipy)



