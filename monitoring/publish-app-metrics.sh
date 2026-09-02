#!/usr/bin/env bash
#
# Publish application-level metrics to CloudWatch. Runs every minute from
# cron on the Swarm manager node (installed by install-monitoring.sh).
#
# The CloudWatch agent covers the machine (CPU, memory, disk). This script
# covers what the agent cannot see:
#
#   HealthzUp / ReadyzUp      1 or 0 — the application's own probes, taken
#                             through the frontend nginx so a passing value
#                             proves the whole chain, not just gunicorn
#   ActiveVisitors5m / 15m    distinct people using the store, from
#                             /metrics/activity/ (fed by every replica via
#                             the shared database)
#   <service>ReplicasRunning  running vs desired tasks per Swarm service —
#                             the "container/service availability" number
#
# Environment overrides:
#   BASE_URL      where the store answers        (default: http://localhost)
#   STACK_NAME    Swarm stack name               (default: rmit)
#   NAMESPACE     CloudWatch metrics namespace   (default: RMITStore)
#   AWS_REGION    region to publish into         (default: from instance metadata)
#
set -uo pipefail

BASE_URL="${BASE_URL:-http://localhost}"
STACK_NAME="${STACK_NAME:-rmit}"
NAMESPACE="${NAMESPACE:-RMITStore}"

if [ -z "${AWS_REGION:-}" ]; then
    # IMDSv2; falls back to ap-southeast-2 off-EC2 so the script is testable.
    TOKEN="$(curl -s -m 2 -X PUT http://169.254.169.254/latest/api/token \
        -H 'X-aws-ec2-metadata-token-ttl-seconds: 60' || true)"
    AWS_REGION="$(curl -s -m 2 -H "X-aws-ec2-metadata-token: $TOKEN" \
        http://169.254.169.254/latest/meta-data/placement/region || true)"
    AWS_REGION="${AWS_REGION:-ap-southeast-2}"
fi
export AWS_DEFAULT_REGION="$AWS_REGION"

METRICS=()  # name value [unit]
add_metric() {
    METRICS+=("MetricName=$1,Value=$2,Unit=${3:-Count},Dimensions=[{Name=Stack,Value=$STACK_NAME}]")
}

# --- Application health, taken through the front door ----------------------
probe() {  # probe <path> -> 1 if HTTP 200, else 0
    code="$(curl -s -o /dev/null -w '%{http_code}' -m 5 "${BASE_URL}$1" || echo 000)"
    [ "$code" = "200" ] && echo 1 || echo 0
}
add_metric HealthzUp "$(probe /healthz/)" None
add_metric ReadyzUp  "$(probe /readyz/)"  None

# --- Visitor activity ------------------------------------------------------
activity_json="$(curl -s -m 5 "${BASE_URL}/metrics/activity/" || true)"
if [ -n "$activity_json" ]; then
    read -r v5 v15 <<EOF
$(python3 - "$activity_json" <<'PY'
import json, sys
try:
    d = json.loads(sys.argv[1])
    print(d.get("active_visitors_5m", 0), d.get("active_visitors_15m", 0))
except Exception:
    print("", "")
PY
)
EOF
    [ -n "$v5" ]  && add_metric ActiveVisitors5m  "$v5"
    [ -n "$v15" ] && add_metric ActiveVisitors15m "$v15"
fi

# --- Swarm service availability --------------------------------------------
# `docker service ls` prints replicas as "running/desired" (e.g. 3/3).
while read -r name replicas; do
    [ -z "$name" ] && continue
    running="${replicas%%/*}"
    desired="${replicas##*/}"
    desired="${desired%% *}"   # strips a "(max N per node)" suffix if present
    short="${name#"${STACK_NAME}"_}"
    case "$short" in
        backend)        metric=Backend ;;
        backend-canary) metric=Canary ;;
        frontend)       metric=Frontend ;;
        db)             metric=Database ;;
        *)              continue ;;
    esac
    add_metric "${metric}ReplicasRunning" "$running"
    add_metric "${metric}ReplicasDesired" "$desired"
done < <(docker service ls --format '{{.Name}} {{.Replicas}}' 2>/dev/null \
         | grep "^${STACK_NAME}_" || true)

# --- Ship it ---------------------------------------------------------------
if [ "${#METRICS[@]}" -eq 0 ]; then
    echo "no metrics gathered; nothing to publish" >&2
    exit 1
fi
aws cloudwatch put-metric-data \
    --namespace "$NAMESPACE" \
    --metric-data "${METRICS[@]}"
