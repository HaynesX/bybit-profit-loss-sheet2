#!/bin/bash

set -e

DOCKER_IMAGE_TAG=$1


cd bybit-profit-loss-sheet2

echo "Shutting Down Previous Containers."

sudo docker-compose -f docker-compose-bybit-profit-loss-sheet2.yaml down

cd ..

echo "Deleting previous directory"

rm -rf bybit-profit-loss-sheet2

echo "Cloning Repo"

git clone https://github.com/HaynesX/bybit-profit-loss-sheet2.git

cd bybit-profit-loss-sheet2

echo "Checkout new version"

git checkout tags/$DOCKER_IMAGE_TAG

echo "Starting Docker Container for Image $DOCKER_IMAGE_TAG"

sudo TAG=$DOCKER_IMAGE_TAG docker-compose -f docker-compose-bybit-profit-loss-sheet2.yaml up -d


