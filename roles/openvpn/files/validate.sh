#!/bin/bash

tr_result=$(traceroute google.com | grep '^ 1 ' | awk '{ print $2 }' | awk -F. '{ print $1 }')

if [ "${tr_result}" == '10' ]; then
    exit 0
else
    exit 1
fi