#!/bin/bash

set -eEu
sudo mkdir -p /run/secrets/
for f in telegram_api_id telegram_api_hash twitter_api_key twitter_api_secret twitter_access_token twitter_secret_token imgur_access_token imgur_account_id imgur_client_id imgur_client_secret imgur_refresh_token postgres-password telegram_phone instagram_user_id instagram_access_token; do
    sudo cp ../secrets/$f /run/secrets/
done
