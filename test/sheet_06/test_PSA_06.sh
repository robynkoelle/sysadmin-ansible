#!/bin/bash

# Check if Wiki.js container is running
container_name="wikijs"
running=$(docker ps | grep $container_name)

if [ -z "$running" ]; then
    echo "Wiki.js container is not running. Starting the container..."
    docker start $container_name

    # Wait a few seconds for the container to fully start
    sleep 5
else
    echo "Wiki.js container is running."
fi

# Test if Wiki.js page is accessible
response=$(curl -s -o /dev/null -w "%{http_code}" http://131.159.74.56:60204/)

if [ "$response" -eq 200 ]; then
    echo "Wiki.js is up and running. The web page is accessible."
else
    echo "Failed to access the Wiki.js page. Response code: $response"
fi
