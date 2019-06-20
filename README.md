PENSIONDATA
===========

Pensiondata is configured to run on Heroku and is currently deployed to https://dashboard.heroku.com/apps/pensiondata

To support asynchronous processing for uploaded files there are several services running in a multicontainer docker environment. The services are web (for the app itself), celery (task queue), and RabbitMQ/CloudAMQP (message broker).

To build the app you will need Docker (tested using version 17.09.0-ce) - https://docs.docker.com/engine/installation/

Cloing the Project
------------------
The project is on github here - https://github.com/brightblackbox/pensiondata

To clone the project to a local directory run the following command. This will create a new *pensiondata* directory in the current working directory.

``` git clone https://github.com/brightblackbox/pensiondata ```

Running Locally
---------------
To run locally you will need docker-compose. Docker for Mac and Docker Toolbox already include Compose along with other Docker apps, so Mac users do not need to install Compose separately. If you need to install you can find instructions here - https://docs.docker.com/compose/install/#install-compose

Before running you will need to set local environment variables by creating a *.env* file in the project root using the template below:

``` 
SECRET_KEY=secretkey
DB_NAME=database
DB_USER=database_user
DB_PASSWORD=database_password
DB_HOST=database_host
DB_PORT=database_port
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_HOST_USER=email_host_user
EMAIL_HOST_PASSWORD=email_host_password
DEFAULT_FROM_EMAIL = 'example@email.com'
```

To run, navigate to the project root directory (where the docker-compose.yml file is located).

``` docker-compose build ```

``` docker-compose up -d ```

On Linux, you may need to prefix each of the above docker-compose calls with sudo.

This will build the docker images for the app on your local machine and then start them up in detached mode. More options for docker-compose can be found here - https://docs.docker.com/glossary/?term=Compose

The app can now be accessed at http://127.0.0.1:8000

Deploying to Heroku
-------------------
To deploy to heroku you will need the Heroku CLI (Toolbelt) - https://devcenter.heroku.com/articles/heroku-cli

To deploy the app push the web and celery containers to heroku - https://devcenter.heroku.com/articles/container-registry-and-runtime#pushing-multiple-images

``` $ heroku login ```

``` $ heroku container:login ```

``` $ heroku container:push web celery --recursive --app pensiondata ```

``` $ heroku container:release web celery --app pensiondata ```

On Linux, you may need to prefix each of the above heroku calls with sudo.

Heroku has a resource CloudAMQP that will replace the RabbitMQ service when deployed

In the event of a bad build of other failure, roll back to the previous release.

``` $ heroku rollback --app pensiondata ```

Domain
------
The DNS settings are managed using CloudFlare, the domain is registered with Google Domains

To Do
-----
Set up a CICD pipeline and test/production environments - https://devcenter.heroku.com/articles/pipelines
