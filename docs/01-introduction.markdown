# <span id="sec:intro" label="sec:intro">Introduction</span>

Noise pollution is an increasing threat to the well-being and public
health of city inhabitants . It has been estimated that around 90 % of
New York City (NYC) residents are exposed to noise levels exceeding the
Environmental Protection Agencies (EPA) guidelines on levels considered
harmful to people . The complexity of sound propagation in urban
settings and the lack of an accurate representation of the distribution
of the sources of this noise have led to an insufficient understanding
of the urban sound environment. While a number of past studies have
focused on specific contexts and effects of urban noise , no
comprehensive city-wide study has been undertaken that can provide a
validated model for studying urban sound in order to develop
long-lasting interventions at the operational or policy level.

In 2017 the NYC 311 information/complaints line \[1\], received 447,090
complaints about noise, up 6.3 % from 2016. NYC has tried to regulate
sources of noise since the 1930s and in 1972 it became the first city in
the U.S. to enact a noise code . As a result of significant public
pressure, a revised noise code went into effect in 2007 . This
award-winning code, containing 84 enforceable noise violations, is
widely-considered to be an example for other cities to follow . However,
NYC lacks the resources to effectively and systematically monitor noise
pollution, enforce its mitigation and validate the effectiveness of such
action. Generally, the Noise Code is complaint driven. The NYC
Department of Environmental Protection (DEP) inspectors are dispatched
to the location of the complaint to determine the ambient sound level
and the amount of sound above the ambient, where a notice of violation
is issued whenever needed. Unfortunately, the combination of limited
human resources, the transient nature of sound, and the relative low
priority of noise complaints causes slow or in-existent responses that
result in frustration and disengagement. The extent of the noise problem
in NYC, its population, and ever-changing urban soundscape provides an
ideal venue for the long term monitoring and ultimately, an enhanced
understanding of urban
sound.

# <span id="sec:sonyc" label="sec:sonyc">Sounds Of New York City Project</span>

At the Sounds Of New York City or SONYC project, we have deployed a
network of over 50 low-cost acoustic sensor nodes across NYC to
facilitate the continuous, real-time, accurate and source-specific
monitoring of urban noise . Some of these nodes have been operational
since May of 2016, resulting in the accumulation of vast amounts of
calibrated sound pressure level (SPL) data and it’s associated metrics.
Cumulatively to date, 52 years of SPL and 26 years of raw audio data has
been collected from the sensor network. This data can be used to
identify longitudinal patterns of noise pollution across urban settings
. Using the inferences from this data, decision makers at city agencies
can strategically utilize the human resources at their disposal, i.e. by
effectively deploying costly noise inspectors to offending locations
automatically identified by the network . The continuous and long term
monitoring of noise patterns allows for the validation of the effect of
this mitigating action in both time and space, information that can be
used to understand and maximize the impact of future action. By
systematically monitoring interventions, one can understand how often
penalties need to be imparted before the effect becomes long-term. With
sufficient deployment time, 311 noise complaint patterns can also be
compared to the network’s data stream in a bid to model and ultimately
predict the occurrence of noise complaints. The overarching goal would
be to understand how to minimize the cost of interventions while
maximizing noise mitigation. This is a classic resource allocation
problem that motivates much research on smart-cities initiatives,
including this
one.

# Remote sensing

Remote sensor networks have been a focus of research for at least 60
years. The majority of recent research focuses on the performance
characteristics of networks with respect to their networking strategies
or power consumption, as the majority of examples are battery reliant .
Remote acoustic sensor networks allow for the collection of longitudinal
acoustic data from a collection of static locations. The abilities of
these networks are often dictated by their price points. High–cost
commercially available static noise monitoring solutions such as Bruel
and Kjaer’s (B\&K) Noise Sentinel system , provide highly accurate SPL
measurements, wireless data transmission and a web portal for real–time
data visualization. These have been used for the long-term monitoring
and reduction of air traffic noise around NYC airports with a deployment
of 32 noise monitoring stations . The cost of these networks limit their
scalability and deployability, with each sensor costing upwards of
$15,000 USD. Typically these networks are rented to a client at the cost
of $105 USD per day. At these prices, a modestly sized network of 32
sensor locations as previously mentioned would result in an annual cost
of around $1.23 Million USD. However, at these prices, B\&K does offer a
guarantee of greater then 95% uptime of the sensor network with dedicated
support. These networks are used to ensure that major airports are in
compliance with local air noise codes.

New York City noise has been the focus of a plethora of studies
investigating: noise levels in relation to air pollutants and traffic ,
noise exposure from urban transit systems  and noise exposure at street
level . All of these highlight the fact that noise is an
underrepresented field in urban health and found that average levels of
outdoor noise at many locations around the city exceed federal and
international guidelines set to protect public health. Sensing of noise
conditions using 56 relatively low cost logging sound level meters
(SLMs) was investigated in , where general purpose SLMs were used to log
SPL measurements over the period of one week. These type of deployments
can help to identify noise patterns over short periods of time with
respect to other factors such as traffic intensity, but are lacking in
their ability to monitor noise over longer duration’s. Long term noise
monitoring is required to allow health researchers to perform better
epidemiological studies of environmental contributions to cardiovascular
disease .

The recent surge in the development of consumer mobile devices, namely
smart-phones has resulted in rapid improvements in processing power,
storage capacity, embedded sensors, and network data rates. The idea
behind the use of consumer devices in mobile remote sensing is to
utilize the sensing, processing and communication capabilities of
consumer smart-phones to enable members of the public to collect and
upload environmental data from their surroundings. This approach
benefits from the use of existing infrastructure (sensing platform and
cellular networks) meaning that deployment costs are effectively zero,
provides unrivaled spatial coverage and also allows for the gathering of
the subjective response to these environments, in-situ. The drawbacks of
this approach mainly lie in the low temporal resolution of its data
resulting from the submission of short term measurements and the quality
of the gathered noise data, as the model, physical and handling
conditions of the smart-phones may not be consistent, resulting in
aggregated environmental data of variable accuracy. A number of
initiatives have sought to crowdsource sound and noise monitoring using
mobile devices . Their apps are typically limited to logging geo-located
instantaneous sound pressure level measurements.

A Spanish team describe their example of a mobile acoustic sensor
network in a 2016 paper . Their aim was to facilitate the creation of
real-time urban noise maps using bus mounted noise sensors. These
sensors would be battery operated and transmit bandwidth heavy noise
data via Wi-Fi and lighter remote control data via a 2G cellular
connection. This ambitious project faced many challenges, not least the
issue of differentiating between the noise of the bus each sensor was
mounted to and the surrounding noise of interest. Their communications
challenges were also unique as they were relying on opportunistic
connectivity from free and open Wi-Fi networks that the bus would pass
through during the run of its route. This presents a number of
challenges when designing for maximal data yield and network resilience.

The majority of sensor network studies in the literature are rather
short in length and low in scale. An example of a longer duration study
focused on noise came from Piper in 2017 . This highly relevant study
focuses on the data collection from a network of 16 low-cost noise
monitoring stations based around a Raspberry Pi 2B single board
computer. One minute resolution noise data was collected across a six
month period at a construction site in London. The availability or
uptime of the sensor network is discussed with favorable values of 67.6%
to 97.8%. Power failures and adverse weather conditions were seen to
have an effect on uptime. The study was also able to generate some
useful inference on the noise conditions of the localized site, proving
the efficacy of longitudinal noise sensor network deployments for the
understanding of noise patterns.

In a non-acoustical example, a team from Intel Research Berkeley and MIT
created a sensor network deployed and managed by non-technical end
users. In their 2004 paper , they describe the design, evaluation and
lessons learned from a real-world deployment of 23 nodes in the canopy
of a single tree for a period of 20 days. Their battery powered sensor
nodes monitor environmental parameters such as light, temperature,
humidity and air pressure. Their team focused on the data yield of the
network with a particular emphasis on the network routing analysis and
its subsequent power consumption. This short term deployment resulted in
node level data yields ranging from 22% to 75% with an active node duty
cycle of 6.6% with data sampled from the environment every 30s. The
authors suggest that the likely cause of data loss is through network
collisions where multiple sensors transmit data simultaneously,
overloading the network. They recommend implementing fault tolerance at
all stages of a deployed sensor network and ensuring that testing is
performed at scale to anticipate a wider gamut of failures. Of note is
their call for detailed monitoring of sensor networks to better
understand failures and the state of individual sensors around the
occurrence of these.

An extreme example of remote sensing of active volcanoes in , highlights
some of the challenges in building robust and reliable sensor networks
where maintenance is extremely difficult. In this example, 13, $3000 USD
each, battery powered sensing stations were air-dropped into and around
the crater of Mount St. Helens, connected via a low frequency mesh
network for multi-hop data transmission and node control. These sensors
were tasked with monitoring and transmitting the seismic and ash plume
activity of the volcano in real-time, and were studied over a 6 week
period. Throughout this period, the data yield or uptime of the network
ranged between 34 to 93.6%. The team mainly observed issues with
software faults and connectivity either due to lightning strikes on
their radio antennas or diurnal fluctuations in signal propagation
strength. To combat these, a combination of hardware additions and
multiple levels of system monitoring with automatic recovery from
software faults was employed. Despite the extreme nature and difference
in application of this deployment, many commonalities are observed
across these examples of remote sensor networks.
Section [\[sec:common\_challenges\]](#sec:common_challenges) discusses
some of these and the ways in which they can addressed.

The Array of Things Project  is an ambitions effort to create a large
sensor network covering Chicago that is capable of sensing a large
variety of physical data points. The project utilizes an alternative
high availability infrastructure, Waggle . Our infrastructure is
designed to have as little custom code as possible, making heavy use of
existing open source projects. Waggle, while it still makes use of some
off the shelf products, utilizes many custom software components. Our
design chooses aloud us to quickly set up a reliable backed and enabled
us to obtain the long term reliability data that we present here.

The sensor network deployments in the reviewed literature are typically
short in duration and very localized to a particular area. Their obvious
validity aside, none have reported on longitudinal deployments across
very large geographical areas, something that is scarcely reported in
the literature. Long term sensor network deployments bring with them a
multitude of complications that must be overcome to ensure a successful
data yield. The following sections will detail the architecture of our
resilient sensor network.