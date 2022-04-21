#!/bin/bash

curl -s ipinfo.io/$(curl -s ifconfig.me) | jq -r '.country'