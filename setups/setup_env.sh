#!/bin/sh

set -e

echo DB_NAME=$DB_NAME >> ~/todo_api/.env
echo DB_USER=$DB_USER >> ~/todo_api/.env
echo DB_PASS=$DB_PASS >> ~/todo_api/.env
echo SECRET_KEY=$SECRET_KEY >> ~/todo_api/.env
echo ALLOWED_HOSTS=$HOST_DNS >> ~/todo_api/.env