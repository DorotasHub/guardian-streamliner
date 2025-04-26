#!/bin/bash

sam build

sam deploy \
  --config-file samconfig.toml \
  --parameter-overrides GuardianApiKey=$(grep GUARDIAN_API_KEY .env | cut -d '=' -f2)