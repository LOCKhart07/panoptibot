#!/bin/bash

USER_NAME=$(whoami)
REPO_PATH=$(pwd)
INPUT_FILE="panoptibot.service.template"
OUTPUT_FILE="panoptibot.service"

# Create panoptibot.service
sed -e "s/{user}/$USER_NAME/g" \
    -e "s|{repo_path}|$REPO_PATH|g" \
    "$INPUT_FILE" > "$OUTPUT_FILE"

# Stop service if it is running
if systemctl is-active --quiet panoptibot.service; then
    SERVICE_RUNNING=true;
    sudo systemctl stop panoptibot.service;
else
    SERVICE_RUNNING=false;
fi;

# Copy new panoptibot.service
sudo cp panoptibot.service /etc/systemd/system/panoptibot.service;

# Reload service if it was running
sudo systemctl daemon-reload;
if [ "$SERVICE_RUNNING" = "true" ]; then
    sudo systemctl start panoptibot.service;
fi