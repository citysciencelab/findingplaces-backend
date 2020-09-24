#!/bin/sh

docker stop fp_geo_instance
docker rm fp_geo_instance
docker run --name fp_geo_instance -d -p 90:80 -p 9080:8080 -p 9081:8081 fp_geo
docker logs -f fp_geo_instance