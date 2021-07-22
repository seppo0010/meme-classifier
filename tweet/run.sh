#!/bin/bash
set -Eeux

while true; do
    date
    cd /tweet && python3 main.py
    sleep 36000
done
