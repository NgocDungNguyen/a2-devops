#!/usr/bin/env bash
#
# One-shot monitoring setup for a Swarm node on Amazon Linux 2023.
# Run as ec2-user from the repository root:
#
#   sudo bash monitoring/install-monitoring.sh
#
# It does three things:
#   1. Installs and starts the CloudWatch agent (CPU / memory / disk / swap,
#      published to the CWAgent namespace with an InstanceId dimension).
#   2. Installs publish-app-metrics.sh under /opt/rmit-monitoring/.
#   3. Adds a cron entry running it every minute (RMITStore namespace).
#
# Prerequisite: the instance profile must carry the CloudWatchAgentServerPolicy
# managed policy — infrastructure/main.yml attaches it to EC2S3AccessRole.
#
set -euo pipefail

if [ "$(id -u)" -ne 0 ]; then
    echo "run me with sudo" >&2
    exit 1
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR=/opt/rmit-monitoring

echo "==> Installing the CloudWatch agent"
dnf install -y -q amazon-cloudwatch-agent

echo "==> Applying agent configuration"
mkdir -p /opt/aws/amazon-cloudwatch-agent/etc
cp "${REPO_ROOT}/monitoring/cloudwatch-agent-config.json" \
   /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json
/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
    -a fetch-config -m ec2 -s \
    -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json

echo "==> Installing the application-metrics publisher"
mkdir -p "$INSTALL_DIR"
cp "${REPO_ROOT}/monitoring/publish-app-metrics.sh" "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/publish-app-metrics.sh"

echo "==> Scheduling it every minute"
dnf install -y -q cronie
systemctl enable --now crond
cat > /etc/cron.d/rmit-app-metrics <<'CRON'
# Application metrics for the RMIT Store CloudWatch dashboard.
* * * * * root /opt/rmit-monitoring/publish-app-metrics.sh >> /var/log/rmit-app-metrics.log 2>&1
CRON
chmod 644 /etc/cron.d/rmit-app-metrics

echo "==> Done. First datapoints appear within two minutes:"
echo "    CWAgent namespace   — CPU, memory, disk (this instance)"
echo "    RMITStore namespace — health probes, visitors, service replicas"
echo "    Dashboard: deploy infrastructure/monitoring.yml if you have not."
