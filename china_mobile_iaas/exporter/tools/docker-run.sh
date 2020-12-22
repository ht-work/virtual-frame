#!/usr/bin/env bash

prometheus_path="/data/prometheus"
prometheus_path_config="${prometheus_path}/config"
prometheus_path_data="${prometheus_path}/data"
docker ps | grep 'prom/prometheus-linux-amd64'
if [ $? -ne 0 ]; then
    [ ! -d $prometheus_path ] && mkdir -p $prometheus_path

    [ -d $prometheus_path_config ] && rm -rf $prometheus_path_config
    cp -rf prometheus/config $prometheus_path_config

    [ ! -d $prometheus_path_data ] && mkdir -p $prometheus_path_data

    docker run -u root -d --name iaas-prom --restart=always -p 10003:9090  \
        -v $prometheus_path_config/prometheus.yml:/etc/prometheus/prometheus.yml  \
        -v $prometheus_path_config/rule.yml:/etc/prometheus/rule.yml  \
        -v $prometheus_path_data:/prometheus  \
        prom/prometheus-linux-amd64:v2.21.0
fi


mysql_path="/data/iaas"
mysql_path_data="${mysql_path}/data"
docker ps | grep 'mysql' &> /dev/null
if [ $? -ne 0 ]; then
    [ ! -d $mysql_path ] && mkdir -p $mysql_path
    [ ! -d $mysql_path_data ] && mkdir -p $mysql_path_data

    docker run --name iaas-mysql --restart=always -p 3306:3306 -e MYSQL_ROOT_PASSWORD=root \
            -v $mysql_path_data:/var/lib/mysql -d mysql:5.7
fi


exit 0
