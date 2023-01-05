#!/bin/bash

alertname="$1"
hostname="$5"
losspattern="$3"
rtt="$4"
target="$2"

api_url="https://homelabapi.example.com/smokeping"
api_key="abc123def456ghi789j0abc123def456ghi789j0"

subject="SmokePing ($alertname)"
message="$target ($hostname) $losspattern"
url="https://example.com"
priority="1"
source="SmokePing"

data="{
       \"api_key\": \"$api_key\",
       \"subject\": \"$subject\",
       \"message\": \"$message\",
       \"url\": \"$url\",
       \"priority\": \"$priority\",
       \"source\": \"$source\",
       \"alertname\": \"$alertname\",
       \"hostname\": \"$hostname\",
       \"losspattern\": \"$losspattern\",
       \"rtt\": \"$rtt\",
       \"target\": \"$target\"
      }"

curl -s \
     -X POST \
     -H "Content-type: application/json" \
     -d "$data" \
     "$api_url"
