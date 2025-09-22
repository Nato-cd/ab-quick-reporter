#!/bin/bash

# A script to extract and summarize key metrics from an Apache Bench (ab) output file.

if [ -z "$1" ]; then
    echo "Usage: $0 <path_to_ab_results_file>"
    exit 1
fi

INPUT_FILE="$1"
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File not found at ${INPUT_FILE}"
    exit 1
fi

# normalize line endings to avoid /bin/bash\r issues
TMP=$(mktemp)
tr -d '\r' < "$INPUT_FILE" > "$TMP"

# Extract key metrics (anchored where appropriate)
REQUESTS_PER_SECOND=$(grep -E "^Requests per second:" "$TMP" | awk '{print $4}')
TIME_PER_REQUEST_MEAN=$(grep -E "^Time per request:" "$TMP" | head -n 1 | awk '{print $4}')
TIME_PER_REQUEST_CONCURRENT=$(grep -E "^Time per request:" "$TMP" | tail -n 1 | awk '{print $4}')
FAILED_REQUESTS=$(grep -E "^Failed requests:" "$TMP" | awk '{print $3}')
TOTAL_REQUESTS=$(grep -E "^Complete requests:" "$TMP" | awk '{print $3}')
TOTAL_TIME=$(grep -E "^Time taken for tests:" "$TMP" | awk '{print $5}')
TRANSFER_RATE=$(grep -E "^Transfer rate:" "$TMP" | awk '{print $3}')
PERCENT_90_TIME=$(grep -E "^\s*90%" "$TMP" | awk '{print $2}')

# robust: extract the second numeric column (mean) from Connect/Processing/Waiting
CONNECT_TIME_MEAN=$(awk '/^Connect:/ {n=0; for(i=1;i<=NF;i++){ if($i ~ /^[0-9]+(\.[0-9]+)?$/){ n++; if(n==2){print $i; exit}}}}' "$TMP")
PROCESSING_TIME_MEAN=$(awk '/^Processing:/ {n=0; for(i=1;i<=NF;i++){ if($i ~ /^[0-9]+(\.[0-9]+)?$/){ n++; if(n==2){print $i; exit}}}}' "$TMP")
WAITING_TIME_MEAN=$(awk '/^Waiting:/ {n=0; for(i=1;i<=NF;i++){ if($i ~ /^[0-9]+(\.[0-9]+)?$/){ n++; if(n==2){print $i; exit}}}}' "$TMP")

# Fallbacks if not found
CONNECT_TIME_MEAN=${CONNECT_TIME_MEAN:-0}
PROCESSING_TIME_MEAN=${PROCESSING_TIME_MEAN:-0}
WAITING_TIME_MEAN=${WAITING_TIME_MEAN:-0}
REQUESTS_PER_SECOND=${REQUESTS_PER_SECOND:-0}
TIME_PER_REQUEST_MEAN=${TIME_PER_REQUEST_MEAN:-0}
TIME_PER_REQUEST_CONCURRENT=${TIME_PER_REQUEST_CONCURRENT:-0}
FAILED_REQUESTS=${FAILED_REQUESTS:-0}
TOTAL_REQUESTS=${TOTAL_REQUESTS:-0}
TOTAL_TIME=${TOTAL_TIME:-0}
TRANSFER_RATE=${TRANSFER_RATE:-0}
PERCENT_90_TIME=${PERCENT_90_TIME:-0}

# Prevent division by zero and format percent
if [ -z "$TOTAL_REQUESTS" ] || [ "$TOTAL_REQUESTS" -eq 0 ]; then
  FAIL_PERCENT="0.00"
else
  FAIL_PERCENT=$(awk "BEGIN {printf \"%.2f\", (${FAILED_REQUESTS}/${TOTAL_REQUESTS})*100}")
fi

echo "Summary:"
echo "-------------------------------------"
printf "  Total Requests:          %s\n" "${TOTAL_REQUESTS}"
printf "  Test Duration:           %s seconds\n" "${TOTAL_TIME}"
printf "  Requests per Second:     %s req/s\n" "${REQUESTS_PER_SECOND}"
printf "  Average Latency (Total): %s ms\n" "${TIME_PER_REQUEST_MEAN}"
printf "  90% of requests served in: %s ms\n" "${PERCENT_90_TIME}"
printf "  Failed Requests:         %s (%s%%)\n" "${FAILED_REQUESTS}" "${FAIL_PERCENT}"
echo ""
echo "Additional Metrics:"
printf "  Mean Connection Time:    %s ms\n" "${CONNECT_TIME_MEAN}"
printf "  Mean Processing Time:    %s ms\n" "${PROCESSING_TIME_MEAN}"
printf "  Mean Waiting Time:       %s ms\n" "${WAITING_TIME_MEAN}"
printf "  Transfer Rate:           %s KBytes/s\n" "${TRANSFER_RATE}"

rm -f "$TMP"

