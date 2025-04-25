#!/bin/bash

sam build

sam deploy \
  --stack-name gs-aws-stack \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --parameter-overrides GuardianApiKey=$(grep GUARDIAN_API_KEY .env | cut -d '=' -f2)
