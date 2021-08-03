# Sensor network evaluation

## Data yield & up-time

In its current iteration, the sole purpose of each SONYC sensor node is
the delivery of usable noise data to the project’s ingestion servers. In
order to define data yield, we decided to focus on the node’s ability to
successfully and continuously upload one minute sound pressure level
(SPL) files, as this process occurs continuously throughout the node’s
operational life. A 100% data yield would therefore mean 60
readable/uncorrupted files are present on the storage servers for every
operational hour. To explore this, the data yield was calculated per
hour in 2017 for nodes that were deployed on or before January 1st 2017,
so were expected to be operational for the entire
year.

![<span id="fig:network_yield" label="fig:network_yield">\[fig:network\_yield\]</span>
Sensor network data yield percentage by hour over
2017](images/network_yield.png)

Figure [\[fig:network\_yield\]](#fig:network_yield) shows the data yield
throughout 2017 for 31 nodes deployed across New York City (NYC),
labelled N01–N31, with the total years data yield per sensor shown. The
intensity of the color represents the data yield as a percentage for
each hour, where the node’s are ordered by increasing data yield. Node
yield varies significantly with the lowest performer successfully
transferring 24.2% of its data up-to the highest performer at 99.6%,
with a mean yield of 75.4% and median of 80.5%. The periods of low data
yield could be due to a number of faults. The following list ordered by
frequency of occurrence explains the more common fault types observed in
the field and how these manifest in terms of data yield with reference
to Figure [\[fig:network\_yield\]](#fig:network_yield). Unfortunately,
strict time-stamped logs were not taken when each of these issues was
observed so their severity cannot be directly quantified.

**Connectivity - intermittent/weak internet connectivity resulting in
intermittent data yield or continuous loss caused by Wi-Fi access point
outage, typically localized to particular sensors but can also manifest
across groups of nodes** Node N02 exhibits a weak Wi-Fi signal shown
clearly by its inability to continuously upload data from January to
July. The more sparse data yield periods between July and October were
caused by the outage of the nearby Wi-Fi access point, which caused the
node to switch to a more remote access point, further reducing its Wi-Fi
signal strength and ability to upload its data payload over time. Early
in the year a change to the NYU Wi-Fi security protocols was rolled out,
but only in halls of residence buildings. Nodes N07, N10, N11, N12, N14,
N16, and N20 are all deployed on halls of residence buildings so could
not upload data for around 3 months. Any data that did make it up during
this period was likely due to our team working on the fault and
providing connectivity temporally via other means when at each site.
Faults of this nature are particularly difficult to diagnose as they are
caused by a third party without any prior notification. It took a number
of months to determine what was at fault and interface with the relevant
people at NYU IT to solve the issue.

**Power failure - prolonged periods of data loss in continuous chunks
caused by internal electrical failure of the node or power cable removal
by third party, typically localized to particular sensors** This
occurrence is usually caused by third parties unplugging the power line
of a node. In locations where the node is plugged into an accessible
outlet, a sealed cover is applied to the power outlet in use, however, a
number of instances have been observed where this has been removed and
the node unplugged. During November to the end of December, N04 was
unplugged, resulting in a block of downtime with no data retrieved. N07
experienced power failures throughout the year caused by NYU facility
managers switching off power centrally to the node’s power outlet. N09
was suffering from an intermittent faulty power cable within the devices
housing, which would result in long periods of downtime. Small amounts
of rain water had caused rust to form on one of the power supply input
contacts which seemed to be exacerbated by colder weather.

**Code fault - prolonged periods of data loss caused by code faults at
node - typically localized to particular sensors but can also manifest
network wide** Code faults can produce a number of complex symptoms that
affect node functionality, including: memory leaks, connectivity issues,
and total script crashes. Code bugs are typically caught and remedied in
lab testing, but some edge cases can manifest only when a node is
subjected to the variable conditions after real-world deployment. For
example, N06 was in range of two different Wi-Fi access points and due
to the networking process flow operating within the node, would get
stuck in a cycle of connecting and disconnecting to different Wi-Fi
networks as their relative signal strengths fluctuate over time. When
this occurs continuously the node will fill its local SD card storage
and data loss will occur. Fixes were implemented to ensure that the node
prioritized the access point with the most consistent signal strength
over time. An example of a catastrophic fault where total node failure
occurred was due to the operating system (OS) SD card partition filling
up to 100% with excess OS log generation. This caused the OS to return
error messages to general commands, resulting in its inability to carry
out its data collection and transmission operations. The time for this
fault to manifest was on the order of months as these log files slowly
grew in size. The daily cycling of OS level logging solved this problem.
A notable fault observed resulted in the failure of the SPL logging code
to reset the CSV file causing its uninhibited growth on the TMP folder.
This partition is limited to 50MB in size. When this partition fills to
100%, all subsequent audio file write to disk operations fail and the
device effectively stops collecting data. This process takes around 3
days to enter a failing state where the TMP partition is filled. The
node does not lose its connectivity to the network but cannot generate
data. This fault is explored further in
Section [\[sec:telemetry\]](#sec:telemetry).

**Server level fault - instantaneous loss of small chunks of data caused
by server fault/outage - manifests network wide** This type of fault is
rare but typically has network wide ramifications. All nodes experienced
data loss for two days in May and June 2017 when a server level data
move procedure failed. Node N15’s data survived as it had cached it
locally and uploaded it after the failed procedure was carried
out.

## <span id="sec:telemetry" label="sec:telemetry">Telemetry data analysis</span>

Table [\[tab:telemtry\_analysis\_table\_data\]](#tab:telemtry_analysis_table_data)
lists the fields used in the analysis of the sensor network’s uptime
during 2017 across all sensors by hour. The % complete column refers to
the amount of data retrieved versus the maximum possible amount which is
equal to: total number of sensors (31) times days in 2017
365 times hours in a day (24) = 271560. Uptime was a
posthoc calculation so is 100% complete, other fields were either
intermittently uploaded throughout the year due to faults or
additionally, in the case of: data usage, var-log usage, and the Wi-Fi
fields; collection did not begin until February of
2017.

|                              |                             |                                 |                       |                      |                       |                       |
| :--------------------------- | :-------------------------- | :------------------------------ | :-------------------- | :------------------- | :-------------------- | :-------------------- |
| **<span>Description</span>** | **<span>% complete</span>** | **<span>Possible range</span>** | **<span>Mean</span>** | **<span>STD</span>** | **<span>Min.</span>** | **<span>Max.</span>** |
| Uptime                       | 100                         | 0–100                           | 75.4                  | 42.8                 | 0                     | 100                   |
| CPU load (1 min)             | 79                          | 0–4                             | 1.16                  | 0.22                 | 0.04                  | 2.74                  |
| CPU temp (C)                 | 79                          | 0–100+                          | 41.7                  | 9.4                  | 5.7                   | 82.9                  |
| RAM usage                    | 79                          | 0–100                           | 16.4                  | 4.5                  | 7.9                   | 43.2                  |
| Running processes            | 79                          | 0–1000+                         | 107.2                 | 5.5                  | 100                   | 143                   |
| TMP usage                    | 78                          | 0–100                           | 4.3                   | 18.9                 | 0                     | 100                   |
| Data usage                   | 71                          | 0–100                           | 4.1                   | 10.4                 | 0.3                   | 99.9                  |
| Var-log usage                | 71                          | 0–100                           | 11.3                  | 21.5                 | 0.2                   | 100                   |
| Wi-Fi signal quality         | 71                          | 0–100                           | 94.4                  | 9.9                  | 17.5                  | 100                   |
| Wi-Fi signal strength        | 71                          | 0–100                           | 81.5                  | 13.5                 | 26.5                  | 100                   |

Telemetry fields used in analysis across all nodes in 2017 by
hour<span id="tab:telemtry_analysis_table_data" label="tab:telemtry_analysis_table_data">\[tab:telemtry\_analysis\_table\_data\]</span>

In order to investigate the conditions around a node’s inability to
successfully perform its duties, all node’s uptime and telemetry data
was merged and split by an uptime binary category. This split grouped
all rows with uptime of 100%/hour as ‘high’ and all those with less than
100%/hour as ‘low’. This split results in 201,326 high rows versus
70,234 low rows. A random sample was taken from the high group that
matched the size of the low group and the mean of each groups values
for: mean, STD, minimum and maximum, were calculated for each of the
hourly telemetry
variables.

|                                         |                        |    |                       |                         |                      |                       |                       |
| :-------------------------------------- | :--------------------: | -: | :-------------------- | :---------------------- | :------------------- | :-------------------- | :-------------------- |
| **<span>Description</span>**            | **<span>Count</span>** |    | **<span>Mean</span>** | **<span>Median</span>** | **<span>STD</span>** | **<span>Min.</span>** | **<span>Max.</span>** |
| \*<span>CPU load (1 min)</span>         | \*<span>18,456</span>  | Hi | 1.17                  | 1.17                    | 0.38                 | 0.48                  | 2.07                  |
|                                         |                        | Lo | 1.07                  | 1.06                    | 0.33                 | 0.50                  | 1.89                  |
| \*<span>CPU temp ( C)</span>            | \*<span>18,456</span>  | Hi | 42.24                 | 43.18                   | 0.61                 | 40.77                 | 43.81                 |
|                                         |                        | Lo | 37.09                 | 36.07                   | 0.60                 | 35.69                 | 38.51                 |
| \*<span>RAM usage</span>                | \*<span>18,456</span>  | Hi | 16.52\*               | 15.22\*                 | 0.29                 | 16.24\*               | 17.96                 |
|                                         |                        | Lo | 16.30\*               | 16.00\*                 | 0.25                 | 16.07\*               | 17.15                 |
| \*<span>Running processes</span>        | \*<span>18,456</span>  | Hi | 107.17                | 106.00                  | 1.24                 | 104.32\*              | 110.56                |
|                                         |                        | Lo | 107.60                | 105.96                  | 1.58                 | 104.45\*              | 111.51                |
| \*<span>TMP usage</span>                | \*<span>16,473</span>  | Hi | 0.71                  | 0.50                    | 0.84                 | 2.17                  | 4.03                  |
|                                         |                        | Lo | 47.90                 | 1.06                    | 1.10                 | 72.13                 | 49.86                 |
| \*<span>Data usage</span>               | \*<span>12,977</span>  | Hi | 3.74                  | 0.50                    | 0.06                 | 3.54                  | 3.57                  |
|                                         |                        | Lo | 11.85                 | 3.10                    | 0.10                 | 11.79                 | 11.92                 |
| \*<span>Var-log usage</span>            | \*<span>12,977</span>  | Hi | 10.28                 | 3.50                    | 0.12                 | 10.61                 | 10.83                 |
|                                         |                        | Lo | 21.10                 | 8.40                    | 0.29                 | 20.98                 | 21.26                 |
| \*<span>Wi-Fi signal quality</span>     | \*<span>12,977</span>  | Hi | 94.47                 | 98.91                   | 2.21                 | 80.43                 | 97.81                 |
|                                         |                        | Lo | 91.90                 | 98.21                   | 2.81                 | 77.84                 | 95.91                 |
| \*<span>Wi-Fi signal strength</span>    | \*<span>12,977</span>  | Hi | 81.57                 | 79.12                   | 1.77                 | 71.75\*               | 84.80                 |
|                                         |                        | Lo | 82.50                 | 80.59                   | 2.14                 | 72.30\*               | 85.82                 |

High/low uptime split by hour across telemetry values (\* indicates a
value that does **not** significantly differ between groups at the
\< 0.001 level using a Mann Whitney U
test)<span id="tab:telemtry_split_high_low" label="tab:telemtry_split_high_low">\[tab:telemtry\_split\_high\_low\]</span>

Table [\[tab:telemtry\_split\_high\_low\]](#tab:telemtry_split_high_low)
shows the summary statistics for the high/low split groups for all of
the gathered telemetry values during 2017. The count values vary as the
gathering of certain parameters began later in the year. The majority of
statistics between groups differ significantly when tested using a
non-parametric Mann Whitney U comparison. The distribution of this data
is typically heavily skewed, for example, TMP usage during normal
operation idles for most of the time around 0.7% but will shoot up to
100% over a number of days in the event of a particular code failure.
This skew is also evident in the large differences between mean and
median values for the parameters in the low group: TMP usage, Data
usage, and Var-log usage. The low group also shows far more erratic
behaviour in these parameters. In the Data usage case, this comes as a
result of the nodes inability to upload data successfully so more data
is cached locally as it retries the upload in cases of weak Wi-Fi
connectivity.

Generally weak Wi-Fi signals result in the nodes inability to upload the
larger data files at \> 150KB, but the node status/telemetry payload is
considerably smaller at 1KB. In the case of extremely weak Wi-Fi
signals, no uploads complete successfully meaning no telemetry data is
logged. This means that Wi-Fi related sensor network issues are
typically lacking in telemetry data for post-hoc diagnosis. An
interesting inference can be made from the Wi-Fi quality telemetry data
as shown in Figure [\[fig:sig\_qual\]](#fig:sig_qual). Signal quality
drops as more clients connect to the same access point (AP). This
particular node is mounted outside a classroom space and next door to a
seminar room and workspace for students. Excessive Wi-Fi traffic can
result in increased packet loss which can manifest in reduced data
upload rates at an effected node. It is vital to ensure there is
adequate signal strength headroom to account for these inevitable drops
in signal quality when a space and an AP becomes saturated with Wi-Fi
traffic.

![Wi-Fi signal quality for single sensor over 24 hours (July 10th
2017)](images/sig_qual.png)

<span id="fig:sig_qual" label="fig:sig_qual">\[fig:sig\_qual\]</span>

CPU load is slightly higher in the high group with more variation in
general. This suggests that nodes in the low group may have code faults
that result in certain operations failing, resulting in lower CPU usage
and less variation in usage as the code fails to run through its cycle
of data creation, encryption and storage.

![CPU temperature for single sensor over 24 hours (July 10th
2017)](images/cpu_temp.png)

<span id="fig:cpu_temp" label="fig:cpu_temp">\[fig:cpu\_temp\]</span>

CPU Temperature is a useful parameter for node health monitoring due to
the thermal throttling features of the OS. Its value is heavily
influenced by CPU load and is offset by ambient temperature.
Figure [\[fig:cpu\_temp\]](#fig:cpu_temp) gives an example of the CPU
temperature over 24 hours of a node in July 2017. The solar heat gain
experienced for two periods when the sun directly hits the node’s
housing results in CPU temperature increase of around 5C.

RAM usage can reveal memory leaks over time, however, the
non-significant differences between the high/low groups suggests this
parameter is not varying between groups. The number of running processes
can indicate failing code that is creating a number of dead or zombie
processes that will eventually clog up the system. There was no
indication during 2017 that the low group exhibited excessive process
creation over the high group,suggesting that this fault type was not
present.

Large fluctuations in TMP usage are a result of a code bug that causes
data to accumulate on the 50MB TMP partition. Var-log usage increases
are usually caused by ongoing issues with data upload and difficulties
when writing to a full TMP partition. The OS increases its logging under
these conditions which can result in excessive log size increases. It is
critical to ensure that log files do not grow to fill their partitions
as this can result in adverse script and node behaviour. The rotation of
log creation on a daily schedule for example can ensure this doesn’t
happen. In the case of the SONYC network, all logs are copied to SD card
storage at midnight and uploaded for future investigative
use.

