
# <span id="sec:acoustic_sensor_nodes" label="sec:acoustic_sensor_nodes">Acoustic sensor nodes</span>

This section details the hardware and software components that
constitute the current version of the acoustic sensor node, including
the deployment, data collection and networking strategies
employed.

## <span id="sec:hardware" label="sec:hardware">Hardware</span>

The acoustic sensor nodes primarily consist of off-the-shelf hardware to
drive down the overall cost of each node.
Figure [\[fig:main\_components\]](#fig:main_components) shows the core
node components (shown at relative scale to each other). The popular
Raspberry Pi 2B single-board-computer (SBC) sits at the core of the node
running the Linux Debian based Raspbian operating system, providing all
main data processing, collection and transmission functionality. The
choice of the Raspberry Pi over the plethora of other SBC choices is
mainly due to the maturity and thus stability of the Raspbian operating
system and the large online community that has been developed over the
six years of the Raspberry Pi’s existence. This kind of community
support has proven to be invaluable throughout the development of the
sensor node as it results in faster operating system kernel updates and
a wealth of useful information online to help solve issues. The majority
of nodes make use of a 2.4/5 GHz 802.11 b/g/n USB Wi-Fi adapter for
internet connectivity, however, a number of nodes also employ a low-cost
power-over-ethernet (POE) module which provides internet connectivity
and power over a single ethernet cable. Initially, only 2.4 GHz Wi-Fi
modules were used, but in some locations with high levels of ambient
2.4 GHz traffic such as those close to high-rise residential buildings
connectivity was intermittent. This prompted the use of dual band
2.4/5 GHz USB Wi-Fi modules to allow for the use of the less congested
5 GHz bands if needed. To further enhance Wi-Fi signal strength, we make
use of directional antennas as shown in
Figure [\[fig:main\_components\]](#fig:main_components). These are more
sensitive on-axis, so can be pointed at the nearest Wi-Fi access point,
increasing signal strength and helping to reduce the negative effects of
unwanted ambient radio frequency (RF) signals.

![Acoustic sensor node deployed on New York City
street](images/node_deployed.jpg)

<span id="fig:node_deployed" label="fig:node_deployed">\[fig:node\_deployed\]</span>

The aluminum housing of the sensor as seen in
Figure [\[fig:node\_deployed\]](#fig:node_deployed), provides further
RFI shielding and resistance to solar heat gain. The bird spikes provide
protection from damaging droppings on the node and reduces the chance of
birds picking at the microphone windshield. The physical deployment of
the sensor nodes is discussed in
Section [\[sec:deployment\]](#sec:deployment).

![Main part list for complete node at relative scale (excluding
housing)](images/main_components.jpg)

<span id="fig:main_components" label="fig:main_components">\[fig:main\_components\]</span>

The sensing module (shown in more detail in
Figure [\[fig:edited\_annotated\_top\]](#fig:edited_annotated_top)) is
mounted at the end of the gooseneck to the custom microphone mount and
covered by the windshield for wind protection. The flexible gooseneck
covers the microphones USB cabling and allows for the positioning of the
microphone for node mounting on horizontal or vertical surfaces such as
window ledges or walls. The custom microphone mount provides a top hood
for the microphone to reduce the chances of rain water dripping down the
microphone modules front face and into the port. The mount’s rear ports
eliminate the chance of acoustic resonance within the mount’s internal
cavity, which could color the microphones signal at certain frequencies.

![Digital acoustic sensing module detail with main component
annotations](images/edited_annotated_top_circle_points)

<span id="fig:edited_annotated_top" label="fig:edited_annotated_top">\[fig:edited\_annotated\_top\]</span>

The custom sensing module in
Figure [\[fig:edited\_annotated\_top\]](#fig:edited_annotated_top) is
based around a digital microelectromechanical systems (MEMS) microphone.
These were chosen for their low cost, consistency across units and size,
which can be 10x smaller than traditional devices. The model utilized
here has an effective dynamic range of 32–120 dBA ensuring all urban
sound pressure levels can be effectively monitored. It was calibrated
using a precision grade sound-level meter as reference under low-noise,
anechoic conditions, and was empirically shown to produce sound pressure
level (SPL) data at an accuracy compliant with the IEC 61672-1 Type-2
standard  that is required by most US and national noise codes. This
procedure is outlined for an earlier version of the sensor in . This
digital microphone contains, within its shielded housing, an
application-specific integrated circuit (ASIC) which performs the analog
to digital conversion of the microphone’s AC signal to a 1-bit pulse
density modulated (PDM) digital signal. This early stage conversion to
the digital domain means there is the absolute minimum of low level
analog signal moving around the circuit, resulting in superior external
radio frequency interference (RFI) and localized electromagnetic
interference (EMI) rejection. EMI from low-cost power supplies and the
SBC are further reduced by the voltage regulator and array of
capacitors, designed to filter out any AC noise on the DC input power
rail. The PDM signal from the MEMS microphone is fed to the
Microcontroller where it is converted to a pulse-code modulated signal
(PCM), filtered to compensate for the microphones frequency response and
fed via USB audio (connector shown unpopulated in
Figure [\[fig:edited\_annotated\_top\]](#fig:edited_annotated_top)) to
the master device, which in this case is our SBC. The enumeration of the
sensing module as a USB audio device means it is SBC agnostic so has the
potential to work with any USB enabled master SBC. The unpopulated JTAG
connector allows the microcontroller to be flashed with updated firmware
if required using an external programmer, however, on module power-up it
will briefly hold in a bootloader mode allowing the firmware to be
updated via USB. This allows for future remote firmware updates
over-the-air, administered by the SBC, via USB to the module’s
microcontroller. Before deployment the component side of the sensing
module is sealed with liquid electrical tape to ensure resting water
doesn’t corrode the components or printed circuit board (PCB) traces.
Silver traces were selected to reduce the chances of any corrosion
spreading throughout the board. The PCB has extensive ground planes that
run across each side for effective RFI and localized EMI shielding. The
entire base of the microcontroller is soldered to this plane which acts
as a heat-sink to spread its generated heat across the PCB. A positive
side effect of this is the heating of the closely neighboring MEMS
microphone. Whilst temperature variations are likely to have a minimal
impact on the microphones sensitivity, it aids in maintaining a
relatively constant temperature on the microphone diaphragm, reducing
the effects of water condensation and the possibility of impaired
operation in the event of water freezing anywhere near the microphone
and forcing components out of place.

Whilst no extensive study of the sensing module’s resilience under
controlled conditions has been carried out, a small number were
retrieved from the field after periods of 3, 6 and 12 months of
deployment throughout varying seasons.
Figure [\[fig:comp\_ref\_dut\]](#fig:comp_ref_dut) shows the deviation
in sensitivity across frequency when compared to the average response of
a batch of 10 non-deployed/clean modules.

![Deviation in microphone sensitivity for retrieved modules with varying
deployment durations in
months](images/comp_ref_dut.png)

<span id="fig:comp_ref_dut" label="fig:comp_ref_dut">\[fig:comp\_ref\_dut\]</span>

The sensitivity deviations shown in
Figure [\[fig:comp\_ref\_dut\]](#fig:comp_ref_dut) seem to manifest at
frequencies above 1 kHz and become more severe at frequencies above
10 kHz. The deployment duration also results in more pronounced high
frequency sensitivity deviations, however, at their worst these exhibit
maximum shifts of approximately 1 dB from a non-deployed module’s response.
This would have a negligible impact on the overall SPL accuracy of the
system, as these minimal variations at higher frequencies above 10 kHz
contribute less to the A-Weighted calculation of SPL with it’s mid
frequency bias. This is a promising finding and suggests that the
resiliency of these modules to wide environmental variations over long
periods of time is high. However, further laboratory controlled analysis
is required to quantify the effects of extreme environmental conditions
on the operation of these
modules.

## <span id="sec:software" label="sec:software">Software implementation</span>

The software running on the node can be divided into four independent
modules:

  - Capture

  - Network

  - Telemetry

  - SysCmdExec

### Capture

This module is responsible for an end-to-end process of recording audio,
extracting sound pressure level (SPL) data, performing encryption and
writing data to disk. A logical flow of the process can be explained
diagrammatically as:

![Logical flow of Capture
module<span style="color: red">(placeholder)</span>](images/sonyc_recorder.png)

The audio capture is performed in a separate process, asynchronous to
other tasks, making sure that the raw audio being captured is not
impeded by any long-running process. The raw 16 bit audio is recorded
perpetually at 48KHz to alternating data buffers that are cycled
between, every 10 seconds.  
Every second, the A, C and Z frequency weighted sound pressure level of
the raw data is also determined. This sub-second procedure call can
sometimes overshoot its computing time by a few micro seconds depending
on the available CPU cycles. In order to make sure the original buffer
can be released back to the recorder in-time, the contents of the raw
buffer are copied to a new string buffer in memory and a reference to it
is passed to the thread computing these SPL values which are then
written to the ramdisk as an ascii file.  
Every 10 seconds, the original data buffer is written to ramdisk as a
’wav’ file which is then converted to flac file format with maximum,
near-lossless, compression. After the raw audio has been compressed, the
encryption sub-module takes over encrypting the flac audio with a
symmetric 4096 bit key. This key is in turn asymmetrically encrypted
using a 4096 bit cryptographic key. These encrypted files are then
archived and compressed; ready to be uploaded to the SONYC ingestion
servers.

### <span id="sec:network" label="sec:network">Network</span>

The networking module is responsible for keeping the sensor node
connected to the network. This module is responsible for connecting the
sensor nodes to either wired or wireless network depending on the
available connectivity options without human intervention. If connected
to a wireless access point, it is up to this module and its sub-modules
to constantly be aware of the ever changing wireless environment and
take an informed decision of switching between the white-listed access
points to be able to provide the sensor node with the most reliable
connectivity option at any given time.  
This module is also responsible for activating different firewall rules
depending on the different physical and virtual network connectivity
situation.  
Different sub-modules can be diagrammatically represented as:

![Different sub-modules of networking
module<span style="color: red">(placeholder)</span>](images/sonyc_network_manager.png)

The **AP monitor**, **internet monitor** and **VPN monitor** are the sub
processes responsible for monitoring the access points in the vicinity,
the internet connectivity, and SONYC VPN network connectivity.  
**AP monitor**: If no wired connection exists, the netmonitor takes
decisions on connecting to different access points based on the the
signal and link quality of the different access points. AP monitor
indicates the presence of all the white-listed access points that can be
connected to and the netmonitor keeps check on the attributes like
signal strength and link quality, combination of which, serves as a
proxy for the WiFi signal quality. The netmonitor ranks these access
points and if the strongest access point contends its position, the
netmonitor begins the procedure for switching over to the new access
point.  
One of the crucial design aspects of the Networking module is the
implementation of *sonyc-lifeline*. SONYC nodes are always on the look
out for a *sonyc-lifeline* WiFi beacon. If they find one in their
vicinity, they stop all their networking activity, tear down the
connections gracefully and hop on to this secure access point. This
helps the instrumentation team perform an on-site maintenance with
minimal physical intervention and maintain the sensor uptime. This
feature has enabled the on-field engineers troubleshoot for problems
conveniently, without physically being connected to the sensor node.
**internet monitor**: This sub process is responsible for constantly
checking the internet connectivity by creating a TCP socket to servers
like Google’s DNS servers (which employs Anycast routing so that nodes
will always get low latency response). The result of this test is a
conclusive proof of a working or non-working WiFi link (working, in this
case, means able to access inter/external network). If the internet
monitor cannot create socket connection for consecutive requests then
the netmonitor takes the matter in its hands and begins procedure of
connecting to the next best access point until internet monitor is
successful in creating socket connection to these servers.  
**VPN monitor**: Once the test from internet monitor establishes the
fact that the connected WiFi access point can provide internet
connectivity, the OpenVPN client creates a virtual TUN (point-to-point)
IP link with SONYC’s VPN network. Netmonitor also applies certain
firewall rules on the node. Once the virtual TUN link is active, this
sub process asks internet monitor to renounce its monitoring duties and
itself begins monitoring by creating TCP sockets to SONYC’s internal
servers.  
**Uploader**
<span id="subsubsec:Uploader" label="subsubsec:Uploader">\[subsubsec:Uploader\]</span>:
Uploader, as the name suggests, is responsible for performing POST
requests to one of the SONYC’s ingestion servers (selected randomly at
runtime). The Uploader script performs inter-process-communication (IPC)
with the VPN monitor and internet monitor sub processes to identify
whether the link is stable enough to being the upload procedure. Once it
has identified the link, it uploads the files & the telemetry data
\[[8.2.3](#subsubsec:Telemetry)\] and verifies the server response.
Finally, after verification, it deletes the successfully uploaded files
from the flash storage. If, for some reason, the upload fails midway or
encounters a timeout while uploading, the uploader sub process will
back-off for a second and try again.

### Telemetry

This module is responsible for collecting telemetry data on the node and
uploading it as a *status\_ping* to the SONYC’s ingestion server every
couple of seconds. The telemetry data is collected for things like:

  - CPU stats: reporting of average CPU utilization over 1 minute, 5
    minutes and 15 minutes helps us visualize and identify any
    abnormality in the working of the sensor and prevent them from going
    down.

  - RAM stats: Just like CPU stats, visualized information on the
    available free memory helps us identify any memory leaks and bugs in
    the code or a fault with the sensor node.

  - WiFi: Current WiFi conditions in the urban canyon like link quality
    and signal strength helps us identify any abnormality in the network
    and the radio antenna while also serving as a proxy to peak hours in
    the RF spectrum, helping us shape the deployment strategy.

  - Disk Utilization: The storage stats like disk utilization of certain
    directories helps us keep tabs on the working of the sensor node.
    Any abnormal behavior is flagged and alerted.

  - Network stats: These provide information about all the network
    interfaces and the stats on network packets that are flowing in and
    out of the sensor node.

  - USB stats: We are using a USB MEMS device as a microphone and a USB
    WiFi NIC card. Collecting stats on all the plugged in USB devices
    helps make sure that these two devices are connected and also that
    there has not been any tampering with the sensor node by connecting
    a foreign USB device.

  - Position stats: SONYC nodes that are in-situ are hard coded with
    their geo positions, whereas the mobile nodes have a USB GPS sensor
    that reports the current position of the sensor node.

  - Git stats: SONYC source code is version controlled using Git. This
    stat helps make sure that the hash of the running commit on the node
    matches the desired commit hash.

  - SPL Level status: This contains the A, C and Z frequency weighted
    SPL data which is useful for returning a real time information on
    the noise.

All of the above data is uploaded as a json body via Uploader
\[[\[subsubsec:Uploader\]](#subsubsec:Uploader)\].  
A complete flow of the above mentioned *status\_ping* is illustrated in
Figure [\[fig:sonyc\_status\_ping\]](#fig:sonyc_status_ping).

![Telemetry
Data<span style="color: red">(placeholder)</span>](images/sonyc_status_ping.png)

<span id="fig:sonyc_status_ping" label="fig:sonyc_status_ping">\[fig:sonyc\_status\_ping\]</span>

### SysCmdExec

This module is responsible for executing system related commands. One of
the crucial responsibilities of this module is to make sure the disk
utilization never crosses a certain percentage, defined as a threshold.
In the event that the sensor node has intermittent or no network
connectivity, the Capture module will start filling up the disk. Once
the disk utilization crosses the aforementioned threshold limit, the
deletion policy of SysCmdExec would kick in and start freeing up the
disk space by first removing the old log files, then strategically
deleting the interleaved encrypted audio files and finally by deleting
the interleaved SPL data files. This module is also capable of running
system commands depending on the server response to the Uploader’s
\[[\[subsubsec:Uploader\]](#subsubsec:Uploader)\] POST requests.  
The above modules have been tested to work independently and reliably
but not all edge cases can be covered and sometimes bugs causing memory
leaks are hard to debug. To ensure that these processes are always
running, we have implemented a *process\_monitor* watchdog that
continuously monitors the working of the above processes/ modules and
the system resources being used by each of these processes. If, for some
reason, any process’s system resource utilization exceeds a certain
threshold, the *process\_monitor* restarts the group responsible for the
modules.  
A working flow of the watchdog can be diagrammatically represented in
Figure [1](#fig:process%20monitor)

![Process
Monitor<span style="color: red">(placeholder)</span><span label="fig:process monitor"></span>](images/sonyc_process_monitor.png)

## <span id="sec:deployment" label="sec:deployment">Deployment</span>

The physical deployment of the sensor nodes is typically surface mounted
using industrial adhesive to a horizontal or vertical surface such as a
window ledge or wall. Deployments are always external and efforts are
taken to mount the nodes away from existing sources of noise at the
building edge, for example air conditioning units or vents. Care is also
taken to ensure the node has an un-occluded view of the street and is as
far away from main exterior walls as possible to reduce the artificial
boosting of measured SPL levels when too close to large hard surfaces.

![Sensor network deployment map with entire network on left and zoom on
dense Washington Square Park deployment
<span style="color: red">(placeholder)</span>](images/sonyc_sensor_locations.jpg)

<span id="fig:sensor_map" label="fig:sensor_map">\[fig:sensor\_map\]</span>

The initial sensor nodes were deployed opportunistically on New York
University (NYU) buildings. These locations can be seen in
Figure [\[fig:sensor\_map\]](#fig:sensor_map). A general rule of at
least a one block distance between sensor nodes was adhered to, unless
there was a particular point of interest close-by such as a long term
construction project or major roadway. These initial NYU nodes were
densely clustered around the Washington Square Park area in Manhattan,
providing a test-bed for the focused analysis of localized noise issues,
such as the predominance of after hours construction noise complaints .
A number of deployments were carried out in partnership with local
business improvement districts (BIDs). These deployments made use of
bucket lifts to mount nodes on BID owned and maintained light poles,
usually greater than 15 feet from the ground. These types of deployment
are difficult to access for maintenance so measures have to be taken to
ensure continuous uptime and the ability to remotely troubleshoot
issues. Some of these measures have been described in
Section [\[sec:network\]](#sec:network), such as the *sonyc-lifeline*
strategy for close proximity node connection and repair in the event of
a software issue.

The primary limits on deployment locations is the node’s reliance on a
wired power connection and close enough proximity to a Wi-Fi access
point. To open up more potential deployment locations across NYC, a
partnership was developed with a major provider of public Wi-Fi. This
partnership enabled deployments in more diverse locations where their
Wi-Fi networks were broadcast. With this requirement satisfied, it was
easier to successfully approach other partners who could provide
deployment locations with mounting possibilities and power. With reduced
data transmission requirements the possibility of cellular connectivity
becomes viable, allowing for enhanced deployment ranges and locations.
This is a current work in progress and will be discussed in
Section [\[sec:future\_work\]](#sec:future_work).

An often underestimated consideration in deploying our sensor nodes is
the requirement for a street-level sign (shown in
Figure [\[fig:deployment\_sign\]](#fig:deployment_sign)) briefly
outlining the research that is going on. This must be located close-by
the deployed node so passersby are aware that acoustic data is being
recorded and provides them with a QR code and link to the project’s
frequently asked question (FAQ) site\[2\] for more information.
Permissions to deploy these signs are typically harder to get, as they
are public facing and more conspicuous than the sensors. However, the
importance of these signs cannot be overstated. The upfront transparency
of displaying the signage can go a long way to alleviate any privacy
concerns city inhabitants may have as it provides accessible information
on the motivations behind the project, it’s goals, and steps taken to
mitigate these concerns.

![<span id="fig:deployment_sign" label="fig:deployment_sign">Street-level signage mounted in close proximity to sensor node
location for public
information</span>](images/deployment_sign.png)

More recent deployments have been primarily driven by the existence of
localized sources of high-impact noise such as large building
constructions, raised subway lines, or extensive road works as
identified by the proliferation of noise complaints in the area. The
time and effort required to secure permission to deploy a node with the
relevant owner of the infrastructure you are mounting to means that
priority must be given to high-impact sites where the node will be
providing the most value to the research and/or project stakeholders.
The time and money required to build sensor nodes can be dwarfed by the
time and cost required to gain the necessary permissions to deploy and
then maintain these sensor nodes as the network expands over time. In
Section [\[sec:maintenance\]](#sec:maintenance), we discuss the process
of sensor network maintenance and upkeep and the ways in which this
process was carried
out.

## <span id="sec:maintenance" label="sec:maintenance">Monitoring and maintenance</span>

A record of each node is stored using Directus, a headless Content
Management System (CMS), which provides a web interface for managing
database entries, as well as a REST API for programmatic data access.
This is where basic meta data is stored for the node including the FQDN,
name of the sensor or location deployed, date deployed, life stage
(Active, Testing, Retired, etc.), geographic location, and engineer
notes. The notes contain details about sensor changes made on
maintenance visits, details about how and where it was mounted, and any
idiosyncrasies about that specific node or deployment that would be
relevant to the sensor engineer who needs to provide maintenance (e.g.
Wall mounted - 3M tape and Gorilla Glue, Access requires lab personnel,
Mounted under metal awning, etc.). In addition, the last status data
received from each node is stored in this database for fast access,
pulled from ElasticSearch every 3 seconds via a daemon. This eliminates
the need to perform time-intensive, historic ElasticSearch queries on
page load.

In order to maintain network uptime, it is necessary that we are able to
oversee the health of the network. Directus is considered "headless",
meaning that it decouples the database management from the front-end
rendering to allow for more flexibility when it comes to how the
information is displayed. The main dashboard was designed with at a
glance summary info, which can display the current status of all nodes
on one page. This is custom built using Flask as a back-end server for
retrieving status data, which is accessed using the Directus API. The
front-end is rendered using d3.js which displays a table of statistics
describing the overall health of the network, a map displaying all
active node deployment locations, and a sortable, filterable table
listing each node and relevant information about the node’s health such
as time since last update, WiFi quality, data usage, etc. Each node has
links to its Directus entry form and a Grafana dashboard, described
next.

A dedicated dashboard for each node is rendered using Grafana, a data
visualization platform specializing in time-series data. This dashboard
displays a grid of plots detailing the node’s operation over time,
including WiFi strength and quality, CPU usage, CPU temperature,
A-weighted sound pressure level, the current AP, etc.

In order to be able to be more reactive with addressing node faults, we
use Grafana’s alerting system with which you can define alerts on each
graph using custom designed thresholds. These alerts are sent via a
Slack channel which can send a custom message depending on the alert and
optionally an image of the affected graph at the time of the alert.
Another method of logging issues involves logging all node faults as
GitHub issues automatically so that failures can be more efficiently and
systematically addressed. This is done using a script that watches the
incoming node logs, looks for logged errors, and posts them to GitHub
using their API.

At it’s current iteration v5.2.0-beta3 (commit: 30c882c), Grafana
doesn’t support alerting using dashboard templating variables, meaning
that dropdowns can’t be used to allow a single dashboard to select
between all FQDNs while still providing alerting. To enable alerting, a
single dashboard needs to be created for every node. Doing so manually
is not a scalable way of maintaining dashboards, so a script was created
that pulls the JSON content from a template dashboard and generates a
separate template for each node. The generation script uses Jinja2
templating variables to inject data from Directus into the rendered
dashboard, allowing us to show the title, the engineer notes, a map of
the position, and an image taken of the deployed node. This script is
triggered to run every time the Directus database is manually
changed.
