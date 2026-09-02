#!/usr/bin/env bash
#
# Canary deployment driver for the RMIT Store Swarm stack.
#
# The mechanism: `backend` (stable) and `backend-canary` share the network
# alias `api` with endpoint_mode dnsrr, so the frontend nginx round-robins
# across every backend task of both services. Traffic share therefore equals
# replica share — 9 stable + 1 canary tasks puts ~10% of requests on the new
# build. /api/version/ reports what each task is running (the version and git
# commit are baked into the image at build time), so the split is verifiable
# from outside the swarm.
#
#   canary.sh start <image> [percent]   put <image> in front of ~percent of
#                                       traffic (default 10)
#   canary.sh status [samples]          sample /api/version/ and tally which
#                                       build answered (default 20 samples)
#   canary.sh promote                   roll the canary image out to the
#                                       stable service (health-gated, one
#                                       task at a time, auto-rollback), then
#                                       retire the canary
#   canary.sh rollback                  retire the canary, restore stable scale
#
# Environment overrides:
#   STACK_NAME        (default: rmit)
#   BASE_URL          where /api/version/ is reachable (default: http://localhost)
#   STABLE_REPLICAS   steady-state stable scale (default: 3)
#
set -euo pipefail

STACK_NAME="${STACK_NAME:-rmit}"
BASE_URL="${BASE_URL:-http://localhost}"
STABLE_REPLICAS="${STABLE_REPLICAS:-3}"

STABLE_SVC="${STACK_NAME}_backend"
CANARY_SVC="${STACK_NAME}_backend-canary"

usage() { sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; exit 2; }

version_of() {  # version_of <service> -> image currently configured
    docker service inspect "$1" --format '{{.Spec.TaskTemplate.ContainerSpec.Image}}'
}

sample_versions() {  # sample_versions <n> -> tally of /api/version/ answers
    local n="$1" i
    for i in $(seq 1 "$n"); do
        curl -s --max-time 5 "${BASE_URL}/api/version/" || true
        echo
    done | sort | uniq -c | sort -rn
}

cmd="${1:-}"; shift || true
case "$cmd" in

start)
    IMAGE="${1:?usage: canary.sh start <image> [percent]}"
    PERCENT="${2:-10}"
    if [ "$PERCENT" -lt 1 ] || [ "$PERCENT" -gt 50 ]; then
        echo "percent must be between 1 and 50" >&2; exit 2
    fi
    # 1 canary task; enough stable tasks to dilute it to ~PERCENT.
    CANARY_TASKS=1
    STABLE_TASKS=$(( (CANARY_TASKS * (100 - PERCENT) + PERCENT - 1) / PERCENT ))

    echo "==> Canary: ${IMAGE} on ~${PERCENT}% of traffic"
    echo "    (${STABLE_TASKS} stable task(s) + ${CANARY_TASKS} canary task(s))"

    docker service scale --detach "${STABLE_SVC}=${STABLE_TASKS}"
    docker service update --image "$IMAGE" --detach "$CANARY_SVC" >/dev/null
    docker service scale "${CANARY_SVC}=${CANARY_TASKS}"

    echo "==> Waiting for the canary task to pass its health check..."
    for _ in $(seq 1 30); do
        state="$(docker service ps "$CANARY_SVC" --filter desired-state=running \
                 --format '{{.CurrentState}}' | head -1)"
        case "$state" in Running*) break ;; esac
        sleep 5
    done
    docker service ps "$CANARY_SVC" --filter desired-state=running

    echo
    echo "Canary is live. Watch it with:"
    echo "    $0 status"
    echo "then either:  $0 promote   or:  $0 rollback"
    ;;

status)
    SAMPLES="${1:-20}"
    echo "==> Configured images"
    echo "    stable: $(version_of "$STABLE_SVC")"
    echo "    canary: $(version_of "$CANARY_SVC")"
    echo "==> Running tasks"
    docker service ls --filter "name=${STACK_NAME}_backend" \
        --format 'table {{.Name}}\t{{.Replicas}}\t{{.Image}}'
    echo "==> ${SAMPLES} samples of ${BASE_URL}/api/version/"
    sample_versions "$SAMPLES"
    ;;

promote)
    IMAGE="$(version_of "$CANARY_SVC")"
    echo "==> Promoting ${IMAGE} to the stable service"
    echo "    (one task at a time, start-first, health-gated, auto-rollback)"
    docker service update --image "$IMAGE" "$STABLE_SVC"
    echo "==> Retiring the canary and restoring steady-state scale"
    docker service scale "${CANARY_SVC}=0" "${STABLE_SVC}=${STABLE_REPLICAS}"
    echo "==> Post-promotion check"
    sample_versions 5
    ;;

rollback)
    echo "==> Retiring the canary — 100% of traffic returns to the stable build"
    docker service scale "${CANARY_SVC}=0" "${STABLE_SVC}=${STABLE_REPLICAS}"
    sample_versions 5
    ;;

*) usage ;;
esac
