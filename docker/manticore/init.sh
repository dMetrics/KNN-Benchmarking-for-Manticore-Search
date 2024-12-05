#!/usr/bin/env bash
command="mysql -e 'CREATE CLUSTER DMETRICS_FTS_1'"
max_retry=10
counter=0
echo "Executing: ${command}"
sleep 3
for ((i=1; i<=$max_retry; i++));
do
  sleep 2
  OUTPUT=$(eval "${command} 2>&1")
  RC=$?
  if [[ "$OUTPUT" =~ .*"DMETRICS_FTS_1".* ]]; then
    echo "Exiting RC: ${RC} since cluster has been created -> more info: ${OUTPUT}"
    break
  fi
done