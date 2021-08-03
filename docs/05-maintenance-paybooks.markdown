# Maintenance Playbook

This section describes a number of common tasks needed to maintain and use the SONYC backend. For each of these tasks, this document will describe the steps needed to perform these tasks. Ordered lists will indicate steps that must be taken in order, while unordered lists indicate steps that can be taken in any order. Modified shell input and output will be displayed as code blocks. These may not be exact.

## Status Checks

### Check ElasticSearch Status
There are two steps that can be used to test the status of ElasticSearch. Unless otherwise noted, these can be run on either the ingestion servers or the control server. 

#### Instructions
1. Check to see if ElasticSearch is running on the current node:

   ```bash
   sudo /etc/init.d/elasticsearch-es-01 status
   ```

2. Get a list of all nodes that ElasticSearch is running on (will only work if ElasticSearch is running on the current node):
  
   ```bash
   curl --cacert /etc/ssl/elasticsearch_api/CA.pem \
                --key /etc/ssl/elasticsearch_api/elasticsearch_api_key.pem \
                --cert /etc/ssl/elasticsearch_api/elasticsearch_api.pem \
                https://$(hostname -f):9200/_cat/nodes?v
   ```
    if all the nodes are working it should list the ingestion servers as well as the control servers, with the IPs. Otherwise servers will be missing. 
    Make sure that the control server is not the master. 

#### Example 
If working:

1. Check to see if ElasticSearch is running on the current node:
   ```bash
   $ sudo /etc/init.d/elasticsearch-es-01 status
   * elasticsearch is running
   ```

2. Get a list of all nodes that ElasticSearch is running on

   ```bash
   $ curl --cacert /etc/ssl/elasticsearch_api/CA.pem --key /etc/ssl/elasticsearch_api/elasticsearch_api_key.pem  --cert /etc/ssl/elasticsearch_api/elasticsearch_api.pem https://$(hostname -f):9200/_cat/nodes?v

   ip             heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
   128.238.101.5            86          99  12    4.38    4.75     4.46 mdi       -      ingestion2-sonyc-es-01
   128.238.101.4            61          95  12    4.48    4.08     4.17 mdi       *      ingestion1-sonyc-es-01
   128.238.182.10           44          96  12    0.88    0.89     1.02 i         -      control-sonyc-es-01
   ```

If server is down:

1. Check to see if ElasticSearch is running on the current node:
   ```bash
   $ sudo /etc/init.d/elasticsearch-es-01 status
   * elasticsearch is not running
   ```
 
2. Get a list of all nodes that ElasticSearch is running on

    ```bash
    $ curl --cacert /etc/ssl/elasticsearch_api/CA.pem --key /etc/ssl/elasticsearch_api/elasticsearch_api_key.pem  --cert /etc/ssl/elasticsearch_api/elasticsearch_api.pem https://$(hostname -f):9200/_cat/nodes?v

    ip       heap.percent ram.percent cpu load_1m load_5m load_15m node.role master name
    10.0.1.2           27          17  99  101.98  101.13   101.23 mdi       *      ingestion-server-1-es-01
    10.0.0.2           37          12   0    0.03    0.04     0.05 mi        -      control-server-es-01
    ```
### Check Ingestion Server Status

#### Instructions

* Open an SSH connection to the ingestion server. If you can't connect, contact Tandon IT for support. 
* Use ```ip addr``` to ensure that both the front end (p1p1, 128.238.182.0/24) and back end (p2p1,  128.238.101.0/24) networks are connected and that tun0 and tun1 are up. 
* Check to see if vida-sonyc is mounted using ```mount | grep vida-sonyc```. If nothing appears, then the drive is not mounted. Make sure that the IP address of the mounted drive is in the back end (128.238.101.0/24) network. 
* Make sure there is sufficient free space on the drive: ```df -h | grep sda2```
* Check the space available on the back end: ```df -h | grep vida-sonyc```
* Make sure that the python server logic, file move scripts, and archive scrips are running using ```sudo supervisorctl status```.
* Check the size of the local file cache using ```du -h --max-depth=0 /var/sonyc/datacache/```
* Make sure Nginx is running ```curl -k https://localhost```. This should report that not certificate was sent. 
* Check to see if nodes are connecting to the local host by insuring the hostname is included in recently updated nodes using ```node_last_update | grep $(hostname)```
* Check to make sure dnsmasq is running with ```sudo /etc/init.d/dnsmasq status``` and make sure the control VPN IP is listed in ```sudo netstat -ltnp | grep -w '53'```. Test it by running ```dig @<vpn ip> <fqdn of node connected to server>```.
* Make sure that files are being archived: Wait 24 hours after any changes, and make sure that new tar files are being added to the appropriate directories in /mount/vida-sonyc. Make sure they contain files.
#### Example 

```bash
$ ssh ingestion1-sonyc.engineering.nyu.edu
login as: _____
Authenticating with public key "_________" from agent
Welcome to Ubuntu 14.04.5 LTS (GNU/Linux 4.4.0-124-generic x86_64)

 * Documentation:  https://help.ubuntu.com/

  System information as of Mon Nov 26 15:55:06 EST 2018

  System load:  5.22              Users logged in:     0
  Usage of /:   24.4% of 3.42TB   IP address for p1p1: 128.238.182.11
  Memory usage: 42%               IP address for p2p1: 128.238.101.4
  Swap usage:   20%               IP address for tun1: 10.8.128.1
  Processes:    396               IP address for tun0: 10.8.0.1

  Graph this data and manage this system at:
    https://landscape.canonical.com/

Last login: ______ from ____________

$ ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: em1: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000
    link/ether 18:66:da:ef:ec:5c brd ff:ff:ff:ff:ff:ff
3: em2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000
    link/ether 18:66:da:ef:ec:5d brd ff:ff:ff:ff:ff:ff
4: em3: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000
    link/ether 18:66:da:ef:ec:5e brd ff:ff:ff:ff:ff:ff
5: em4: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000
    link/ether 18:66:da:ef:ec:5f brd ff:ff:ff:ff:ff:ff
6: p1p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:0a:f7:9e:3b:de brd ff:ff:ff:ff:ff:ff
    inet 128.238.182.11/24 brd 128.238.182.255 scope global p1p1
       valid_lft forever preferred_lft forever
7: p1p2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000
    link/ether 00:0a:f7:9e:3b:df brd ff:ff:ff:ff:ff:ff
8: p2p1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 24:8a:07:67:b1:a0 brd ff:ff:ff:ff:ff:ff
    inet 128.238.101.4/24 brd 128.238.101.255 scope global p2p1
       valid_lft forever preferred_lft forever
9: p2p2: <NO-CARRIER,BROADCAST,MULTICAST,UP> mtu 1500 qdisc mq state DOWN group default qlen 1000
    link/ether 24:8a:07:67:b1:a1 brd ff:ff:ff:ff:ff:ff
10: tun1: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN group default qlen 100
    link/none
    inet 10.8.128.1 peer 10.8.128.2/32 scope global tun1
       valid_lft forever preferred_lft forever
11: tun0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN group default qlen 100
    link/none
    inet 10.8.0.1 peer 10.8.0.2/32 scope global tun0
       valid_lft forever preferred_lft forever

$ mount | grep vida-sonyc
RSCH-VS-01-data.poly.edu:sonyc on /mount/vida-sonyc type nfs (rw,addr=128.238.101.20)

$ df -h | grep sda2
/dev/sda2       
                3.5T  855G  2.5T  26% /
$ df -h | grep vida-sonyc
RSCH-VS-01-data.poly.edu:sonyc   60T   39T   22T  65% /mount/vida-sonyc

$ sudo supervisorctl status
SONYC_server_8000                RUNNING   pid 2443, uptime 35 days, 2:00:38
SONYC_server_8001                RUNNING   pid 2445, uptime 35 days, 2:00:38
SONYC_server_8002                RUNNING   pid 2448, uptime 35 days, 2:00:38
SONYC_server_8003                RUNNING   pid 2453, uptime 35 days, 2:00:38
SONYC_server_8004                RUNNING   pid 2454, uptime 35 days, 2:00:38
archive_audio_files              RUNNING   pid 2463, uptime 35 days, 2:00:38
archive_logs_files               RUNNING   pid 2475, uptime 35 days, 2:00:38
archive_spl_files                RUNNING   pid 2464, uptime 35 days, 2:00:38
archive_status_files             RUNNING   pid 2457, uptime 35 days, 2:00:38
archive_test_audio_files         RUNNING   pid 2460, uptime 35 days, 2:00:38
archive_test_spl_files           RUNNING   pid 2468, uptime 35 days, 2:00:38
move_data                        RUNNING   pid 2441, uptime 35 days, 2:00:38

$ du -h --max-depth=0 /var/sonyc/datacache/
2.9G    /var/sonyc/datacache/

$curl -k https://localhost
<html>
<head><title>400 No required SSL certificate was sent</title></head>
<body bgcolor="white">
<center><h1>400 Bad Request</h1></center>
<center>No required SSL certificate was sent</center>
<hr><center>nginx/1.14.0</center>
</body>
</html>

$ node_last_update | grep $(hostname)
sonycnode-b827eb42bd4a.sonyc   ingestion1-sonyc            now         09:20:36PM 11/26/18     0013ef2000e7
...

$ sudo /etc/init.d/dnsmasq status
 * Checking DNS forwarder and DHCP server dnsmasq                                                                                                                                * (running)

$ sudo netstat -ltnp | grep -w '53'
tcp        0      0 128.238.182.11:53       0.0.0.0:*               LISTEN      33506/dnsmasq
tcp        0      0 128.238.101.4:53        0.0.0.0:*               LISTEN      33506/dnsmasq
tcp        0      0 10.8.128.1:53           0.0.0.0:*               LISTEN      33506/dnsmasq
tcp        0      0 10.8.0.1:53             0.0.0.0:*               LISTEN      33506/dnsmasq
tcp        0      0 127.0.1.1:53            0.0.0.0:*               LISTEN      77138/dnsmasq

$ dig @10.8.128.1 sonycnode-b827eb42bd4a.sonyc

; <<>> DiG 9.9.5-3ubuntu0.17-Ubuntu <<>> @10.8.128.1 sonycnode-b827eb42bd4a.sonyc
; (1 server found)
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 11977
;; flags: qr aa rd ra ad; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 0

;; QUESTION SECTION:
;sonycnode-b827eb42bd4a.sonyc.  IN      A

;; ANSWER SECTION:
sonycnode-b827eb42bd4a.sonyc. 0 IN      A       10.8.0.10

;; Query time: 0 msec
;; SERVER: 10.8.128.1#53(10.8.128.1)
;; WHEN: Mon Nov 26 16:37:52 EST 2018
;; MSG SIZE  rcvd: 62


```

### Check Control Server Status

#### Instructions

* Open an SSH connection to the control server. If you can't connect, contact Tandon IT for support. 
* Use ```ip addr``` to ensure that both the front end (eth0, 128.238.182.0/24) and back end (eth1,  128.238.101.0/24) networks are connected and that tun0 and tun1 are up.
* Make sure there is sufficient free space on the drive: ```df -h | grep sda1```
* Check that powerdns recursor is running using ```sudo /etc/init.d/pdns-recursor status``` and attempting to get the IP address of a sensor node connected to each ingestion server.  This can be done using ```dig <node FQDN>```. You can get a list of connected nodes using "node_last_update"
* See if mysql is running ```sudo /etc/init.d/mysql status```
* Check that Apache is running using ```sudo /etc/init.d/apache2 status```
* Check that Nginx is running: ```sudo /etc/init.d/nginx status```
* Make sure the Drupal control panel is running by going to https://control-sonyc.engineering.nyu.edu/sonyc_cp/ with a web browser
* Make sure Kibana is running by going to https://control-sonyc.engineering.nyu.edu/kibana/ with a web browser


#### Example 

```bash
$ ssh control-sonyc.engineering.nyu.edu
login as: ____
Authenticating with public key "_______" from agent
Welcome to Ubuntu 14.04.5 LTS (GNU/Linux 4.4.0-124-generic x86_64)

 * Documentation:  https://help.ubuntu.com/

  System information as of Mon Nov 26 16:25:42 EST 2018

  System load:  0.57                Users logged in:     1
  Usage of /:   15.2% of 133.74GB   IP address for eth0: 128.238.182.10
  Memory usage: 42%                 IP address for eth1: 128.238.101.6
  Swap usage:   0%                  IP address for tun0: 10.8.128.4
  Processes:    245                 IP address for tun1: 10.9.128.4

  Graph this data and manage this system at:
    https://landscape.canonical.com/

83 packages can be updated.
9 updates are security updates.

New release '16.04.5 LTS' available.
Run 'do-release-upgrade' to upgrade to it.

Your Hardware Enablement Stack (HWE) is supported until April 2019.
Last login: ____ from _____

$ ip addr
1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:86:77:74 brd ff:ff:ff:ff:ff:ff
    inet 128.238.182.10/24 brd 128.238.182.255 scope global eth0
       valid_lft forever preferred_lft forever
3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP group default qlen 1000
    link/ether 00:50:56:86:06:eb brd ff:ff:ff:ff:ff:ff
    inet 128.238.101.6/24 brd 128.238.101.255 scope global eth1
       valid_lft forever preferred_lft forever
4: tun0: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN group default qlen 100
    link/none
    inet 10.8.128.4 peer 10.8.128.1/32 scope global tun0
       valid_lft forever preferred_lft forever
5: tun1: <POINTOPOINT,MULTICAST,NOARP,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UNKNOWN group default qlen 100
    link/none
    inet 10.9.128.4 peer 10.9.128.1/32 scope global tun1
       valid_lft forever preferred_lft forever

$ df -h | grep sda1
/dev/sda1       134G   21G  107G  17% /

$ sudo /etc/init.d/pdns-recursor status
 * pdns_recursor is running

$ dig sonycnode-b827eb42bd4a.sonyc

; <<>> DiG 9.9.5-3ubuntu0.18-Ubuntu <<>> sonycnode-b827eb42bd4a.sonyc
;; global options: +cmd
;; Got answer:
;; ->>HEADER<<- opcode: QUERY, status: NOERROR, id: 56473
;; flags: qr rd ra; QUERY: 1, ANSWER: 1, AUTHORITY: 0, ADDITIONAL: 1

;; OPT PSEUDOSECTION:
; EDNS: version: 0, flags:; udp: 4096
;; QUESTION SECTION:
;sonycnode-b827eb42bd4a.sonyc.  IN      A

;; ANSWER SECTION:
sonycnode-b827eb42bd4a.sonyc. 0 IN      A       10.8.0.10

;; Query time: 1 msec
;; SERVER: 127.0.0.1#53(127.0.0.1)
;; WHEN: Mon Nov 26 17:19:07 EST 2018
;; MSG SIZE  rcvd: 73

$ sudo /etc/init.d/mysql status
mysql start/running, process 1308

$ sudo /etc/init.d/apache2 status
 * apache2 is running

$ sudo /etc/init.d/nginx status
 * nginx is running
```

## Apply Changes

### Updating Packages on Servers
Follow the folowing procedure to update the packages on the server. Please note that you should only run it on one server at a time.

#### Instructions

1. Check the status on the server to make sure everything is running as expected.
2. Run ```sudo apt-get update``` on the server
3. Run ```sudo apt-get upgrade``` on the server
4. If the Kernel was updated, restart the server (only one at a time!)
5. Check the status to make sure everything is as expected.


## Troubleshooting

### Can Not SSH Into Server 

#### Instructions
1. Make sure you are on a network that is open to SSHing onto the server. If off campus, you may need to use the VPN.
2. Test the connection from a client and configuration that was able to connect in the past.
3. Contact Tandon IT support. 

### Server Has Wrong IP Addresses or Physical Device is Down

#### Instructions

* Contact Tandon IT support

### vida-sonyc is not Mounted on a Ingestion  Server or Data Access Server or has Wrong IP

#### Instructions

* Contact Tandon IT support

### Insufficient Storage Space on Server

#### Instructions

1. Use ```du --max-depth=1``` to find what is taking up the storage. You can start by running this in the root directory, then recursively running it in subdirectories until you find the issue.
2. If /var/sonyc/datacache/ is the issue, make sure the back end storage is mounted and the move file script is running.
3. if /var/log is the issue, delete the old logs (or all the logs).
4. Otherwise you will need to determine the usefulness of the information stored, and how to best manage it. 

### Back End Storage is Running Low on Space or INodes 

#### Instructions

1. Contact Tandon IT to see if they can allocate more. 
2. Inform the PIs of the situation.

### supervisord Services are Down

#### Instructions

1. Run ```sudo /etc/init.d/supervisord restart``` or use ```supervisorctl``` to start the individual service. 
2. If the service still will not start, examine the logs in /var/log/supervisor/. Note that the "error" and "log" logs may have there names reversed. 

### Nginx is Down

1. Run ```sudo /etc/init.d/nginx```
2. If Nginx still will not start, check logs in /var/log/nginx/

### OpenVPN is down, or 'tun0' or 'tun1' is Missing 

1. Run ```sudo /etc/init.d/openvpn restart```
2. If it fails to restart, examine logs in ```/var/log/openvpn``` and ```/var/log/openvpn-*```
3. Note that you may need to change the logging level in the OpenVPN configuration. This is done by adding the "verb" directive in the corresponding configuration file in ```/etc/openvpn/```. For example, add the directive ```verb 6``` or ```verb 9```.

## Vagrant Test Environment 

### Fix hostname
Due to a bug in the puppet environment, the hosts file may not be ordered correctly. This leads to the failure of the ```hostname``` command.  

#### Instructions
1. edit ```/etc/hosts```:

   2. Move the line corresponding to the top of the file
   3. Add the name of the server after the FQDN. 
   
2. Test ```hostname -f``` to make sure it returns the FQDN. 

#### Example 

Changes to ```/etc/hosts```:

Before:
```hosts
# HEADER: This file was autogenerated at 2018-11-20 22:31:26 +0000
# HEADER: by puppet.  While it can still be managed manually, it
# HEADER: is definitely not recommended.

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost   ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
10.0.1.2        ingestion-server-1.sonyc
127.0.0.1       localhost.localdomain   localhost localhost4 localhost4.localdomain4
::1     localhost6.localdomain6 localhost6 localhost6.localdomain6
10.0.0.2        control-server.sonyc
10.0.1.3        ingestion-server-2.sonyc
10.0.0.3        data-decryption-server.sonyc
10.1.0.2        control-server-backend.sonyc
10.1.1.2        ingestion-server-1-backend.sonyc
10.1.1.3        ingestion-server-2-backend.sonyc
```

After:

```hosts
# HEADER: This file was autogenerated at 2018-11-20 22:31:26 +0000
# HEADER: by puppet.  While it can still be managed manually, it
# HEADER: is definitely not recommended.
10.0.1.2   ingestion-server-1.sonyc ingestion-server-1

# The following lines are desirable for IPv6 capable hosts
::1     ip6-localhost   ip6-loopback
fe00::0 ip6-localnet
ff00::0 ip6-mcastprefix
ff02::1 ip6-allnodes
ff02::2 ip6-allrouters
ff02::3 ip6-allhosts
127.0.0.1       localhost.localdomain   localhost localhost4 localhost4.localdomain4
::1     localhost6.localdomain6 localhost6 localhost6.localdomain6
10.0.0.2        control-server.sonyc
10.0.1.3        ingestion-server-2.sonyc
10.0.0.3        data-decryption-server.sonyc
10.1.0.2        control-server-backend.sonyc
10.1.1.2        ingestion-server-1-backend.sonyc
10.1.1.3        ingestion-server-2-backend.sonyc
```

Output of ```hostname -f```
```bash
$ hostname -f
ingestion-server-1.sonyc
```