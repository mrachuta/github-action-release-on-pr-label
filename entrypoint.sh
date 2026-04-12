#!/usr/bin/env bash

input_token=$1
input_repository=$2
input_pull_request_id=$3
input_mode=$4
custom_tag=""
debug=""

if [[ -n "$5" && "$5" != "false" && "$5" != "FALSE" && "$5" != "False" && "$5" != "0" ]]; then
  custom_tag="--custom-tag $5"
fi

if [[ "$6" == "true" || "$6" == "TRUE" || "$6" == "True" || "$6" == "1" ]]; then
  debug="--debug"
fi

python3 /app/roprl.py --token "$input_token" --repository "$input_repository" --pull-request-id "$input_pull_request_id" --mode "$input_mode" $custom_tag $debug
