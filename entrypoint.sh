#!/usr/bin/env bash

input_token=$1
input_repository=$2
input_pull_request_id=$3
input_mode=$4
debug=''

if [[ "$ACTIONS_STEP_DEBUG" == "true" ]]; then
  debug='--debug'
fi

python3 roprl.py --token "$input_token" --repository "$input_repository" --pull-request-id "$input_pull_request_id" --mode "$input_mode" "$debug"
