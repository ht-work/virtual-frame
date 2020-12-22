#!/usr/bin/env bash

docker images | grep 'prom/prometheus-linux-amd64' &> /dev/null
if [ $? -ne 0 ]; then
    ls ./prometheus/*.tgz &> /dev/null || (echo -e "\033[31m err:\033[0m prometheus image not exist."  && exit 1)

    docker load --input ./prometheus/*.tgz &> /dev/null
fi

docker images | grep 'mysql' &> /dev/null
if [ $? -ne 0 ]; then
    ls ./db/*.tgz &> /dev/null || (echo -e "\033[31m err:\033[0m mysql image not exist."  && exit 1)
    docker load --input ./db/*.tgz &> /dev/null
fi

exit 0
