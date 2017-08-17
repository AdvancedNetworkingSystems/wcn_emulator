#!/bin/sh
BASE_URL="http://ninux-graph.netjson.org"
# put your network topology id here
UUID="49aecbcf-a639-47a7-9f58-e39de5d57161"
# put your network topology key here
KEY="O5VPjS3Z34iCmupO12LDngJAuU0xOcJF"
COLLECTOR_URL="$BASE_URL/api/receive/$UUID/?key=$KEY"
DATA=$(cat $1)
curl -s -X POST -d "$DATA" --header "Content-Type: text/plain" "$COLLECTOR_URL"
