---
trigger: always_on
description: "Memory Safety Gate"
---
## Memory Safety Gate
Before running any build, test, migration, or Docker command, run the following check in the terminal and wait until at least 4000 MB of RAM is available:

`while [ $(free -m | awk '/^Mem:/{print $7}') -lt 4000 ]; do echo "Low RAM, waiting 30s..."; sleep 30; done`