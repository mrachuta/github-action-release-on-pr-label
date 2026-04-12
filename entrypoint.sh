#!/usr/bin/env bash

# GitHub Actions provides all inputs as environment variables with the INPUT_ prefix.
# These names are uppercase by default.
token="${INPUT_TOKEN}"
repository="${INPUT_REPOSITORY}"
pull_request_id="${INPUT_PULL_REQUEST_ID}"
mode="${INPUT_MODE}"
custom_tag="${INPUT_CUSTOM_TAG}"
assets="${INPUT_ASSETS}"
debug="${INPUT_DEBUG}"

CMD=("python3" "/app/roprl.py")
CMD+=("--token" "$token")
CMD+=("--repository" "$repository")
CMD+=("--pull-request-id" "$pull_request_id")
CMD+=("--mode" "$mode")

if [[ -n "$custom_tag" ]]; then
  CMD+=("--custom-tag" "$custom_tag")
fi

if [[ -n "$assets" ]]; then
  CMD+=("--assets" "$assets")
fi

if [[ "$debug" == "true" || "$debug" == "TRUE" || "$debug" == "True" || "$debug" == "1" ]]; then
  CMD+=("--debug")
fi

# Execute the command
"${CMD[@]}"
