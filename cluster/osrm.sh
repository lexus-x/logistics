#!/usr/bin/env bash
# Korean road network for real driving distances, all local: bash cluster/osrm.sh build | serve | stop
# Public OpenStreetMap data comes in; nothing leaves this machine (the server listens on 127.0.0.1 only).
set -euo pipefail
mkdir -p "$(dirname "$0")/../data/osm" && cd "$(dirname "$0")/../data/osm"
IMG=ghcr.io/project-osrm/osrm-backend:v5.27.1
URL=https://download.geofabrik.de/asia/south-korea-latest.osm.pbf
RUN=(docker run --rm --user "$(id -u):$(id -g)" -v "$PWD:/data" "$IMG")
case "${1:-}" in
  build)
    [ -s south-korea-latest.osm.pbf ] || { curl -fsSLO "$URL" && curl -fsSL "$URL.md5" | md5sum -c -; }
    docker pull -q "$IMG"
    "${RUN[@]}" osrm-extract -p /opt/car.lua /data/south-korea-latest.osm.pbf
    "${RUN[@]}" osrm-partition /data/south-korea-latest.osrm
    "${RUN[@]}" osrm-customize /data/south-korea-latest.osrm ;;
  serve)
    docker run -d --name osrm-kr --user "$(id -u):$(id -g)" -p 127.0.0.1:5055:5000 -v "$PWD:/data" "$IMG" \
      osrm-routed --algorithm mld --max-table-size 500 /data/south-korea-latest.osrm ;;
  stop) docker rm -f osrm-kr ;;
  *) echo "usage: $0 build|serve|stop"; exit 1 ;;
esac
