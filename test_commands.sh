#!/bin/bash
echo "=== Testing commands with 10s timeout ==="
timeout 10 pwd && echo "pwd: OK" || echo "pwd: TIMEOUT"
timeout 10 git --version && echo "git: OK" || echo "git: TIMEOUT"
timeout 10 echo "test" && echo "echo: OK" || echo "echo: TIMEOUT"
timeout 10 whoami && echo "whoami: OK" || echo "whoami: TIMEOUT"
timeout 10 date && echo "date: OK" || echo "date: TIMEOUT"
