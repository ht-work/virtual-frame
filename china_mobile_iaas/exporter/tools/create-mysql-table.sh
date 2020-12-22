#!/usr/bin/env bash

mysql -uroot -proot -h127.0.0.1 -P3306 -e "CREATE DATABASE IF NOT EXISTS iaas DEFAULT CHARSET utf8 COLLATE utf8_general_ci;"

exit 0
