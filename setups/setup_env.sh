#!/bin/sh

set -e

echo DB_NAME=$DB_NAME >> .env
echo DB_USER=$DB_USER >> .env
echo DB_PASS=$DB_PASS >> .env
echo SECRET_KEY=$SECRET_KEY >> .env
echo ALLOWED_HOSTS=$HOST_DNS >> .env
