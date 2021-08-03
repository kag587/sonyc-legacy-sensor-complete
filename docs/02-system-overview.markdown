# SONYC’s systems architecture

Our data collection backend consists of a number of ingestion servers, a
backend network, a Storage Area Network (SAN) appliance, a control
server, a data access server, a decryption server, an air-gapped
Certification Authority (CA) server, and front end dashboard.

At a high level, nodes transmit status updates and Sound Pressure Level
(SPL) data to the ingestion servers. This ingestion server keeps a
database of status updates, caches the data, then forwards it to the SAN
for long term storage. The control server provides an tiebreaker and
load balancer for the status database as well as an access point for a
virtual network to communicate with the nodes. The data access servers
allow our researchers to view and access the data stored on the SAN.The
CA server grants cryptographic certificates for the various clients and
nodes. Finally, the front end dashboard gives our instrumentation team
and interested parties the ability view the status of the network and
the individual nodes in a convenient single location.

The ingestion, control, and decryption servers are configured using a
customized Puppet  manifest and module. We utilize Vagrant to create a
test environment and validate the configuration before it goes live. The
front end dashboard runs on a number of Docker\[cite?\] containers.

In this section, we will begin by describing the various servers. In
Section [7](#sec:data-flow) we will describe, in depth, the various data
pathways and control within our systems and security considerations and
trade-offs that went into designing our system.

## Ingestion Servers

The ingestion servers are the heart of the backend. They are the direct
contact point between the backend and the sensor nodes.

Each ingestion server runs two OpenVPN  based Virtual Private Network
(VPN) services. The ingestion VPN connects the ingestion servers to
sensor nodes with sufficient network connectivity. The control VPN
connects the control servers to the ingestion servers and tunnels packet
to the sensor nodes. Each ingestion server has its own VPN IP address
range which is automatically allocated to nodes as they connect. A local
DNS server keeps track of when node connections and disconnections,
allowing for an easy query of connected nodes.

The ingestion servers provide a REST interface for the nodes to upload
data. On each ingestion server, this interface is provided by several
identical WSGI  Python processes along with an Nginx proxy  directing
traffic within the server. Once data is uploaded to the ingestion
server, it is cached to a local SSD drive. Another process transfers the
data to a backend storage system, as allowed by network and storage
bandwidth. Once a data folder is untouched for a 24 hour period, it is
compressed into a single tar archive for easier access.

The ingestion servers also run a distributed Elasticsearch  database
which stores and indexes status updates. This database allow our
administrators to obtain a near real-time view of the entire sensor
network.

The ingestion servers continue operating, albeit in a reduced state, if
other components of the system fail. If the storage appliance goes
offline, the ingestion servers keep caching data locally for several
weeks. If the connection to a quorum of Elasticsearch nodes is lost, the
remainder of the system will continue ingest data, though it will not
update the status database. Besides the storage appliance and
Elasticsearch back-end, each ingestion server operates independently,
leading to native high-availability and scalability.

## Control Server

The control server connects to each of the ingestion server’s control
VPNs. Maintainers log onto the control server and utilize ssh to connect
to each of the connected nodes. A DNS recursor on the control server
aggregates the DNS records from each ingestion server and provides a
uniform query point. Maintainers access nodes by their FQDN without
knowing which ingestion server that node is connected to or which IP
address the node is currently assigned.

The control server runs an Elasticsearch instance which manages load
balancing for queries from the Front End Dashboard. This instance is
also a tiebreaker to prevent split brain when an even number of
ingestion servers are used.

The control server is not considered to be critical for the functioning
of the sensor network. While it is invaluable for mounting and
maintaining the network, the network continues to upload and ingest data
when the control server is offline. As such, the control server is not
configured in a highly available configuration. If such high
availability becomes necessary, multiple control servers can easily be
combined for better fault tolerance.

## Data Access and Decryption Servers

The data access server provides users a direct access the acquired data
without risking any accidental modification of the other servers. The
data access server provides direct read-only access to the SAN. Users
log on to the server and run scripts to organize the reacquired data.
The user then transfers this data to a shared home directory or their
local workstation via SCP.

The data decryption server provide decryption keys for the audio
samples. As discussed in section [\[sec:software\]](#sec:software), each
audio clip is encrypted with a symmetric key which is, in-turn,
encrypted with a public asymmetric key. The corresponding asymmetric
private key is stored on the decryption server. Users, with a valid
client certificate (signed by the CA server), send a REST requests to
the data decryption server for each symmetric key. The server then
returners the decrypted symmetric key, allowing for access to a given
files. Users are expected to keep decrypted data exclusively in RAM,
limiting the risk of lost data.

## Certificate Authority Server

The Certificate Authority (CA) Server is responsible for signing the
certificates for the various services. The CA server is air-gapped. Its
operator needs to physically boot it using an encryption key stored on a
USB dongle. Certificate Signing Requests (CSRs) and associated private
keys are generated on the new host. The CSRs, but not the keys, are
transferred to the CA server using a USB flash drive and signed. The
resulting certificate is then transferred to a networked workstation
using the same USB drive. Finally, the key is uploaded over the network
to the desired host. The entire process can be performed for many nodes
simultaneously in only a few minutes using custom scripts.

Each sensor node requires a single signed client certificate identifying
its FQDN and MAC addresses. Each ingestion server requires four
certificates: a server certificate to identify it to the sensor nodes, a
control VPN server certificate to allow the control server to connect to
it, a frontend Elasticsearch certificate and a backend Elasticsearch
certificate. The control server requires three certificates: one to
connect the control VPN and the two needed to be part of the
Elasticsearch cluster. The Decryption Servers and its clients require
data access certificates. Finally, the Front End User Interfaces need
one front-end Elasticsearch certificate.

## Front End User Interfaces

The Front End User Interfaces provides our instrumentation team and
other interested viewers an overview of the status of each node as well
as a method of controlling those nodes.

The control server provides a custom web dashboard that provides an
overview of the status of all sensor nodes.

An overview page shows details about each active node including its
title, life stage, time since last update, sound level, Fully Qualified
Domain Name (FQDN), indication if the software is up to date, the status
of its microphone, the existence of its cryptographic signature, its
Wi-Fi signal strength, and local storage utilization. The overview page
also has a map with all sensor locations.

Each sensor node also has its own page that displays a number of useful
metrics. These metrics are automatically refreshed every few seconds
allowing team members to monitor a node they are working on in real
time. Each metric contains a link to a graph showing the historic values
of those metrics.

The node’s pages also display notes from the implementation team. These
notes can be modified by the team, and the revision history is stored,
allowing technicians to quickly familiarize themselves with the history
and partialities of a node requiring
maintenance.

# Data Flow

## General data type description<span id="sec:data_description" label="sec:data_description">\[sec:data\_description\]</span>

A sensor node collects three main types of data, in order of priority:
sound pressure level (SPL) values, encrypted 10s audio snippets, and
node status data. SPL data is in the form of a two comma delimited table
files within a tar file for 1s and 0.125s resolution A, C and
un-weighted SPL data generated every minute. These files also contain
single and third octave band SPL values to determine acoustic energy at
discrete points across the audible spectrum. The encrypted audio
snippets are losslessly compressed audio files contained within gzipped
tar files. The node status data is uploaded as a json payload with no
compression due to its small size. These data types are summarized in
Table [\[tab:main\_data\_types\]](#tab:main_data_types).

|                              |                         |                       |                            |                         |
| :--------------------------- | :---------------------- | :-------------------- | :------------------------- | :---------------------- |
| **<span>Description</span>** | **<span>Format</span>** | **<span>Size</span>** | **<span>Frequency</span>** | **<span>Cached</span>** |
| Sound pressure level (SPL)   | tar                     | 150KB                 | 60s                        | yes                     |
| Audio snippets               | tar.gz                  | 500KB                 | 20s                        | yes                     |
| Node status                  | json                    | 1KB                   | 3s                         | no                      |

Main data type summary ordered by descending
priority<span id="tab:main_data_types" label="tab:main_data_types">\[tab:main\_data\_types\]</span>

SPL data is captured continuously and is cached locally in case of
upload failures. Audio data is captured and encrypted around three times
per minute with randomly spaced intervals between recordings to ensure
discontinuity in recordings for privacy reasons. These are also cached
locally for persistence if upload fails. Node status data is uploaded
every three seconds, however, if an upload fails, the data is not
cached, it is refreshed with new data and the upload cycle is repeated
after another three seconds. This data is of low enough priority that
local disk space is not utilized for it.

![A high level overview of the different data and control flows in our
system (blue arrow = data flow, green arrow = control flow)
<span style="color: red">may want to relocate
this</span>](images/sonyc_system.png)

## Primary Data Flow

The primary data path is designed to reliably transmit data from the
sensor nodes to archives within the storage appliance. The SPL and
recording data transmitted through his channel is considered to be the
definitive version and is only used for offline analysis. Accordingly,
the pathway is designed to prioritize dependability over efficiency. The
data is cached at multiple stages and stored until confirmation of a
successful transfer to the next stage.

The sensor nodes transmit files to a random ingestion server via a REST
interface. The sensor waits until it receives a successful transfer
confirmation before deleting a file. If no confirmation is received, the
file may be transferred multiple times.

Before sending a confirmation, the receiving ingestion server caches the
file on a local SSD. This cache allows the upload to continue even if
the SAN environment is unavailable. Even if the SAN is available, using
the local SSD cache allows the upload to complete faster, without being
bottle-necked by the network connection to the SAN.

A separate process is responsible for moving files from the cache to the
storage appliance. The process first checks to ensure that the REST
server has finished the file’s upload and closed the file. Afterward, it
moves the file to the mounted SAN directory using the Linux ’mv -b’
command, which will only delete the original file after the move is
completed and will rename, rather then override, any existing files.
Similar to the, the REST server, the server will continue to attempt to
transfer the file until a successful transfer deletes the file.

A final step in the primary data flow is a housekeeping script which
combines files into a compressed archive. The script looks for folders
that have not been modified for at least a day. It copies the files to
the local SSD and then creates the archives. This archive is copied back
to the SAN in the same directory of the original folder. That archive is
then decompressed to the local SSD. The newly decompressed files are
compared bytewise to the original file still in the SAN. If the files
are identical, the original file is deleted. If all the files in the
folder are deleted, the folder is as well. Multiple instances of this
process run on each ingestion server. The processes lock the folders
they are working on to prevent multiple instances from processing the
same folder at the same time.

The complex archiving process is designed to ensure no data loss. At any
point in time, a full pristine copy of the data exists on the SAN. If
the process is interrupted due to power, network, or some other outage
the worst that can happen is the folder being distributed over multiple
archives with possibly overlapping files. This case is checked for
during data analysis.

## Real Time Data Flow

The Real Time Data Flow is designed to give to give the instrumentation
team an instantaneous overview of the entire sensor network. Unlike the
the Primary Data Flow, a focus is placed on low latency over
reliability. If data can’t immediately be transmitted through the
pipeline, it is discarded. This ensures that when data does make it
through, it is up-to-date and represents the current status of the
sensor.

At a regular interval, each sensor compiles a JSON file with an overview
of its current status. This data normally includes the CPU, Memory and
Disk utilization as well as the CPU temperature, wifi connection info,
and other metrics. However, SPL samples are also sent on a less frequent
basis. The sensor then attempts to send this status file via the REST
interface to a random ingestion server.If the sensor is unable to send
the status update, it is deemed obsolete and discarded.

Upon receipt, the ingestion server attempts to validate the data within
the JSON file. In particular, it attempts to prevent a forged hostname
by comparing the name within the JSON file to the HTTPS certificate. If
the names don’t match, a warning is logged and the certificate’s name is
used.However, a pristine copy of the JSON file is always saved for
retention and logging, in the same manner as the primary data flow.

Once the data has been filtered, the server attempts to save the data to
the Elasticsearch database. This database is distributed across the
ingestion servers, with the control server acting as a tiebreaker in
case of split brain. As such, as soon as it is written to the database,
we consider it available for queries.

![The home page and node page of our custom dashboard
<span style="color: red">(placeholder)</span>](images/web_dashboard_full.PNG)
![The home page and node page of our custom dashboard
<span style="color: red">(placeholder)</span>](images/web_dashboard_node_page_full.PNG)

<span id="fig:web_dashboard_full" label="fig:web_dashboard_full">\[fig:web\_dashboard\_full\]</span>

We provide two methods for visualizing the status updates. The first is
the open source Kibana dashboard. Users can use it to view the status
updates, examine trends, and create graphs. The second is a custom web
dashboard (Figure
[\[fig:web\_dashboard\_full\]](#fig:web_dashboard_full)), which allows
our instrumental team to view the status of all nodes at a glance to
zoom into the status of individual nodes. Additionally, the custom
dashboard function as an inventory management system for nodes, allowing
our team to track their deployment and lifecycle.

## VPN and Control Channel

There are two Virtual Private Networks (VPNs), whose primary purpose is
to allow the instrumentation team direct access to and control of the
sensor nodes. The sensor VPN connects each node to an ingestion server,
while the control VPN connects the control servers to the ingestion
servers.

For load balancing, sensor nodes attempt to connect to a random
ingestion server’s client VPN service. Each ingestion server has a
dedicated IP range which they assign to nodes as they connect, which is
tracked by a DNS service running on the ingestion server.

Once node successfully connects, it remains associated with the same
ingestion server until it loses the connection. Nodes associate the IP
10.254.254.254 with whichever ingestion server it is currently connected
to.

Each ingestion server also has a control VPN service. The control server
connects to each ingestion server through this service. The ingestion
servers act as a bridge between the control and client VPNs. For
convenience, a DNS recursor is run on the control server that
amalgamates the DNS records from all the ingestion servers. Users on the
control server can access any of the connected nodes via its FQDN. In
particular, users can access the shell on a node using ssh.

It should be noted that each ingestion server’s control channel can
function independently from the control server in the case of an outage.
Administrators connected to an ingestion server can connect to all the
nodes currently associated with it.
