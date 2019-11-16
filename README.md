YOLOify Django project based on [Bootstrap 3](http://getbootstrap.com/).

## What's inside?

*   [Django 1.5](https://docs.djangoproject.com/en/1.5/)
*   [South](http://south.readthedocs.org/)
*   [Django Compressor](https://django_compressor.readthedocs.org/en/1.3/) With [LESS](http://lesscss.org/) and [CoffeeScript](http://coffeescript.org/) support.
*   [Celery](http://www.celeryproject.org/)
*   [PIL](http://effbot.org/imagingbook/pil-index.htm)
*   [sorl-thumbnail](http://sorl-thumbnail.readthedocs.org/)

## Installation sequence

It is assumed that you use Ubuntu as the platform for YOLOify deployment and bash as the command line interpreter.

1. Install PostgreSQL, the recommended database backend for YOLOify:

        $ sudo apt-get install postgresql

1. Install Redis server that is used to pass tasks information to Celery:

        $ sudo apt-get install redis-server

1. Install the Memcached server:

        $ sudo apt-get install memcached

1. Install Python PIP to install Python packages:

        $ sudo apt-get install python-pip

1. Install Python development files that are required to compile some Python packages:

        $ sudo apt-get install python-dev

1. Install PostgreSQL development files:

        $ sudo apt-get install libpq-dev

1. Install library for JPEG files manipulation:

        $ sudo apt-get install libjpeg-dev

1. Install latest Python Virtualenv with PIP:

        $ sudo pip install virtualenv

1. Create Python virtual environment for the project, cd into it, and activate it:

        $ virtualenv yoloify-virtualenv
        $ cd yoloify-virtualenv
        $ source bin/activate

1. Clone the code repository and cd into it:

        (yoloify-virtualenv)$ git clone https://bitbucket.org/yoloify/yoloify
        (yoloify-virtualenv)$ cd yoloify

1. Install Python packages required by the YOLOify:

        (yoloify-virtualenv)$ pip install -r requirements.txt

1. Copy the example file for local settings and edit the copy. The most important change is to set the database backend credentials (see below):

        (yoloify-virtualenv)$ cp yoloify/dev.local_settings.py yoloify/local_settings.py
        (yoloify-virtualenv)$ vim yoloify/local_settings.py

1. Setup the database backend:

        (yoloify-virtualenv)$ sudo su - postgres
        postgres$ createuser -D -E -P -R -S yoloify
        Enter password for new role: 
        Enter it again:
        postgres$ createdb -E utf8 -O yoloify yoloify

1. Initialize the database structure:

        (yoloify-virtualenv)$ python manage.py syncdb
        (yoloify-virtualenv)$ python manage.py migrate
        (yoloify-virtualenv)$ python manage.py collectstatic

1. Download the latest Linux binaries of NodeJS from [this page](http://nodejs.org/download/) according to your architecture (32-bit or 64-bit). Unpack the archive and put the files into the virtualenv directory:

        (yoloify-virtualenv)$ tar xvzf <download dir>/node-<NodeJS version>-linux-<Linux architecture>.tar.gz -C /tmp/
        (yoloify-virtualenv)$ rsync -a --progress /tmp/node-<NodeJS version>-linux-<Linux architecture>/ ../

1. Install NodeJS lessc compiler for less files:

        (yoloify-virtualenv)$ npm install -g less

1. To run the background tasks Celery server in development mode run the following command:

        (yoloify-virtualenv)$ celery worker -A yoloify -l info

1. To run the Django server in development mode run the following command:

        (yoloify-virtualenv)$ python manage.py runserver

1. Access the site via url [http://localhost:8000/](http://localhost:8000/).

## Hints and tips

### Generating test data

One can populate the database with randomly generated users and goals with the following commands:

    (yoloify-virtualenv)$ python manage.py populate_users
    (yoloify-virtualenv)$ python manage.py populate_goals

### Clearing the caches

One can clear the Redis cache with the following command:

    (yoloify-virtualenv)$ redis-cli
    127.0.0.1:6379> FLUSHALL
    OK
    127.0.0.1:6379> exit

To clear the Memcached cache run the following command:

    (yoloify-env)$ telnet localhost 11211
    Trying 127.0.0.1...
    Connected to localhost.
    Escape character is '^]'.
    flush_all
    OK
    ^]

    telnet> quit
    Connection closed.


## Postgis Installation and setting of the local_settings.py

1. Install postgis with following command.

        $ sudo apt-get update
        $ sudo apt-get install postgresql-9.3-postgis-2.1

1. Create Postgis extension on existing Database.

        $ createdb  <db name>
        $ psql <db name>
        > CREATE EXTENSION postgis;
        > CREATE EXTENSION postgis_topology;

1. Installing Geospatial libraries

        sudo apt-get install binutils libproj-dev gdal-bin

1. On local_settings.py setup database info like this.

        DATABASES = {
            'default': {
                'ENGINE': 'django.contrib.gis.db.backends.postgis',
                'NAME': 'test_postgis',
        
                'USER': 'postgres',
                'PASSWORD': 'postgres',
                'HOST': '',
                'PORT': '',
            }
        }


## Deploy code to beta server

1. Install requirements (Only one time)

        $ pip install -r ansible/requirements.txt

2. CD to ansible directory

        $ cd ansible

3. Deploy latest code to beta server

        $ sudo ansible-playbook playbooks/app.yml -e "server=dev" -t "deploy" --private-key ~/.ssh/id_rsa