#!/bin/bash

api_url="https://homelabapi.example.com/monit"
api_key="abc123def456ghi789j0abc123def456ghi789j0"

subject="Monit -- $MONIT_EVENT ($MONIT_HOST)"
message=$MONIT_DESCRIPTION
url="https://example.com"
priority="1"
source="Monit"

data="{
       \"api_key\": \"$api_key\",
       \"subject\": \"$subject\",
       \"message\": \"$message\",
       \"url\": \"$url\",
       \"priority\": \"$priority\",
       \"source\": \"$source\",
       \"date\": \"$MONIT_ACTION\",
       \"description\": \"$MONIT_DESCRIPTION\",
       \"event\": \"$MONIT_EVENT\",
       \"host\": \"$MONIT_HOST\",
       \"process_children\": \"$MONIT_PROCESS_CHILDREN\",
       \"process_cpu_percent\": \"$MONIT_PROCESS_CPU_PERCENT\",
       \"process_memory\": \"$MONIT_PROCESS_MEMORY\",
       \"process_pid\": \"$MONIT_PROCESS_PID\",
       \"program_status\": \"$MONIT_PROGRAM_STATUS\",
       \"service\": \"$MONIT_SERVICE\"
      }"

curl -s \
     -X POST \
     -H "Content-type: application/json" \
     -d "$data" \
     "$api_url"
