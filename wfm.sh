#!/bin/bash
JAVA_PATH=$(which java)
LAUNCHER_JAR=$(find ~/wfm-launcher -name "*.jar" | head -1)

if [ -z "$LAUNCHER_JAR" ]; then
    echo "JAR file not found!"
    exit 1
fi

$JAVA_PATH -jar "$LAUNCHER_JAR" "$1"
