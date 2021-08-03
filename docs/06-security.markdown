# Security Considerations and Limitations

We designed our system to resist several different threat models. We
assume that a small number of unknown individual sensors nodes are
physically accessible by adversaries and thus could potentially become
compromised. We assume that all internet traffic, though not the
back-end network, is insecure and is analyzed by adversaries. Finally,
we assume that data stored on the HPC cluster is accessible by curious,
but not hostile, parties.

Each sensor uses a unique client certificate, containing its FQDN, to
communicate with the ingestion server. Compromising the node gives the
attacker access to this certificate, allowing the adversary the ability
to spoof data from the node. However, the adversary is unable to
impersonate other nodes nor compromise the system further. When the
instrumentation team detects the intrusion, they simply revoke the
certificate.

The servers communicate with each other and the sensor nodes over
encrypted channels based on either https or OpenVPN; identifying
themselves with CA signed certificates. Care is taken to follow best
practices regarding cipher selection. Ingestion servers communicate with
the storage appliance through a dedicated and isolated virtual LAN.

We use a shared HPC system to analyze the sound clips. While the
environment has adequate security and file protections to prevent a
hostile actor from gaining access, we can’t ensure that a configuration
error could allow another user to accidentally gain access to the sound
recordings. To prevent such an occurrence, we keep the data encrypted
while on disk and only decrypt it as needed during a computation. The
decryption server authenticates clients utilizing a CA signed
certificate that is stored separately on the HPC cluster.

We would like to institute better logging and auditing on the decryption
server to attempt to limit unauthorized access to the decryption server.
We believe that better logging and preregistration of use would allow us
to handle an adversary gaining full access to the HPC environment.
However, we believe that our local HPC cluster is more then sufficiently
secured, making these upgrades academic.

Our security analysis assumes that that the various servers are properly
secured and have appropriate access policy. However, this challenge is
common to all server setups and thus beyond the scope of this document.
We do wish to note that, to limit the effect of our servers being
physically compromised, the decryption server and data are stored in
separate datacenters.

We assume that no state level actors are attempting to infiltrate our
system. An actor with that level of resources would be able to
compromise the air-gapped CA server utilizing sophisticated attacks,
bypass the physical security in place to protect our server, or utilize
non-public vulnerabilities in our server and open source components.

Finally, we should note that in the process of building the system,
human and programming errors have compromised some security at times. We
recommend that any new system have strong security polices and audits
regarding the storage of private keys and have all usage of cryptography
libraries and systems reviewed and
audited.