#!/usr/bin/env bash

docker-compose down
docker rm -f $(docker ps -a -q)

# DANGER: The following command will remove all your volumes!!!
# docker volume rm $(docker volume ls -q)

docker-compose up -d
