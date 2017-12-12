
PENSIONDATA
===========

Pensiondata is configured to run on Heroku and is currently deployed to https://dashboard.heroku.com/apps/pensiondata

To support asynchronous processing for uploaded files there are several services running in a multicontainer docker environment. The services are web (for the app itself), celery (task queue), and RabbitMQ/CloudAMQP (message broker).

Running Locally
---------------
To run locally you will need Docker (tested using version 17.09.0-ce) - https://docs.docker.com/engine/installation/

You will also need docker-compose. Docker for Mac and Docker Toolbox already include Compose along with other Docker apps, so Mac users do not need to install Compose separately. If you need to install you can find instructions here - https://docs.docker.com/compose/install/#install-compose

Once installed, you can navigate to the project root directory (where the docker-compose.yml file is located) and run the following:

``` docker-compose build ```

``` docker-compose up -d ```

This will build the docker images for the app on your local machine and then start them up in detached mode. More options for docker-compose cna be found here - https://docs.docker.com/compose/reference/up/v                                                            

The app can now be accessed at http://127.0.0.1:8000

Deploying to Heroku
-------------------
To deploy to heroku you will need the Heroku CLI (Toolbelt) - https://devcenter.heroku.com/articles/heroku-cli

To deploy the app push the web and celery containers to heroku - https://devcenter.heroku.com/articles/container-registry-and-runtime#pushing-multiple-images

```  heroku container:push web celery --recursive --app pensiondata ```

Heroku has a resource CloudAMQP that will replace the RabbitMQ service when deployed

Domain
------
The DNS settings are managed using CloudFlare, the domain is registered with Google Domains
