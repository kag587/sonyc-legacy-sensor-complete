#!/bin/bash
fqdn=$(hostname -f)
echo "_______________COPY BELOW THIS LINE_________________"
echo "Node ID: [**\`$fqdn\`**](https://control-sonyc.engineering.nyu.edu/sonyc_cp/)"
DATE=$(date +'%Y-%m-%dT%H:%M:%S')
echo ""
echo "Date dump taken: \`$DATE\`"
echo ""
echo "Linux info: "
echo "\`$(uname -a)\`"
echo ""
echo "Dump filename: \`log_dump_$DATE.tar.gz\`"
tar -cf "./log_dump_$DATE.tar" -C /home/sonyc/sonycnode/logs .
tar -rf "./log_dump_$DATE.tar" -C /var/log syslog
tar -czf "./log_dump_$DATE.tar.gz" -C . "log_dump_$DATE.tar" --remove-files
chown sonyc "./log_dump_$DATE.tar.gz"
echo ""
echo "Filesystem status:"
echo "\`\`\`"
echo "$(df -h)"
echo "\`\`\`"
echo "Wi-Fi status: "
echo "\`\`\`"
echo "$(iwconfig wlan0)"
echo "\`\`\`"
echo "SupervisorCTL status:"
echo "\`\`\`"
echo "$(supervisorctl -c /home/sonyc/sonycnode/utils/supervisord.conf status)"
echo "\`\`\`"
echo "⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻COPY ABOVE THIS LINE⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻⎻"