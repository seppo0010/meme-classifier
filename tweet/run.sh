#!/bin/bash
set -Eeux

while true; do
    echo starting "$(date)"
    cd /tweet && python3 main.py
    echo finished "$(date)"
    sleep 36000
done
