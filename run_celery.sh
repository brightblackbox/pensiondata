#!/bin/sh

# wait for RabbitMQ server to start
sleep 10

celery worker -A apps.common -l info --without-gossip --without-mingle --without-heartbeat

