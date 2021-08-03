# Custom "pristine" Raspbian image setup
The OS used for this project is a modified version of the Raspbian OS. It is created by removing all GUI packages from the base Raspbian version and then installing the dependencies required for this project.  

Create this image on a 2GB SD Card using Raspbian Jessie Lite:

```
Linux 4.1.13-v7+ #826 SMP PREEMPT Fri Nov 13 20:19:03 GMT 2015 armv7l GNU/Linux
```

To revert back to this version on device use the following `rpi-update` sequence:

```
rpi-update ddacb5e91eb5c67bb39df99182b071d7199e7a74
```

## Access control setup

Set SUDO password using:

```bash
sudo passwd
```
Create sonyc user and create home directory:

```bash
sudo adduser sonyc
```

Set password using:

```bash
sudo passwd sonyc <password>
```
Remove the pi user:
```bash
sudo deluser -remove-home pi
```

Edit the sudoers file with the sonyc users permissions. Use:

```bash
su root
```

to login as root. Then:

```bash
sudo visudo -f /etc/sudoers
```

The file should look like this:

```bash
#
# This file MUST be edited with the 'visudo' command as root.
#
# Please consider adding local content in /etc/sudoers.d/ instead of
# directly modifying this file.
#
# See the man page for details on how to write a sudoers file.
#
Defaults    env_reset
Defaults    mail_badpass
Defaults    secure_path="/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"

# Host alias specification

# User alias specification

# Cmnd alias specification

# User privilege specification
root    ALL=(ALL:ALL) ALL

# Allow members of group sudo to execute any command
%sudo   ALL=(ALL:ALL) ALL

# See sudoers(5) for more information on "#include" directives:

#includedir /etc/sudoers.d
sonyc ALL=NOPASSWD: /sbin/reboot
sonyc ALL=NOPASSWD: /usr/bin/apt-get update
sonyc ALL=NOPASSWD: /etc/init.d/networking *
sonyc ALL=NOPASSWD: /sbin/ifup *
sonyc ALL=NOPASSWD: /sbin/ifdown *
sonyc ALL=NOPASSWD: /usr/bin/nano /etc/network/interfaces
sonyc ALL=NOPASSWD: /etc/init.d/sshd *
sonyc ALL=NOPASSWD: /etc/init.d/ssh *
sonyc ALL=NOPASSWD: /bin/ping *
sonyc ALL=NOPASSWD: /sbin/iwlist *
```

Save the file but make sure to save as <b>/etc/sudoers</b> and not <b>/etc/sudoers.tmp</b> which it will default to.

## Networking

Update the USB IDs so wifi module identification using `lsusb` will be easier:

```bash
sudo apt-get update
sudo update-usbids
```
Grab the latest wireless tools and realtek/ralink based module firmware:

```bash
sudo apt-get install wireless-tools
sudo apt-get install wpasupplicant
sudo apt-get install firmware-realtek
sudo apt-get install firmware-ralink
sudo apt-get install firmware-atheros
```


Open /etc/network/interfaces file using nano. It should look like this:

```bash
# interfaces(5) file used by ifup(8) and ifdown(8)

# Please note that this file is written to be used with dhcpcd
# For static IP, consult /etc/dhcpcd.conf and 'man dhcpcd.conf'

# Include files from /etc/network/interfaces.d:
source-directory /etc/network/interfaces.d

auto lo
iface lo inet loopback

iface eth0 inet manual

allow-hotplug wlan0
iface wlan0 inet manual
    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf

allow-hotplug wlan1
iface wlan1 inet manual
    wpa-conf /etc/wpa_supplicant/wpa_supplicant.conf
```

Now, you can setup the Wi-Fi on the SD Card. Edit /etc/wpa_supplicant/wpa_supplicant.conf:

```bash
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="<pref_ssid>"
    psk="<password>"
}
```

Take wlan0 interface down `sudo ifdown wlan0` and then up again `sudo ifup wlan0` to connect to the access point providing internet connectivity.

Create the OPENVPN config file here `/etc/openvpn/ingestion-server.conf` and fill it with:

```bash
# Tunnel options
dev tun
proto udp
nobind
comp-lzo
ca /etc/ssl/sonyc_nodes/CA.pem
user root
# TLS Mode options
cert <path_to_file>
key <path_to_file>
tls-client
remote-cert-tls server
# Client Mode options
client
# Data Channel Encryption options
auth SHA256
cipher AES-128-CBC
# Custom options
remote-random
log /var/log/openvpn-ingestion-server
verb 1
mute 3
crl-verify <path_to_file>
remote <ingestion_url_1>
remote <ingestion_url_2>
```

Create WiFi driver file to disable low power mode for 8192cu based adpators like the USB Edimax EW-7811 Un (which makes SSHing a PITA) and change SSH keep alive settings. First create the file using this command:

```bash
sudo nano /etc/modprobe.d/8192cu.conf
```

Enter this line into the file save, close and reboot:

```bash
options 8192cu rtw_power_mgnt=0 rtw_enusbss=0
```
Add the 8812au 5GHz wireless adaptor driver after you have successfully connected to the internet using the follwing commands:

```bash
sudo wget http://www.fars-robotics.net/install-wifi -O /usr/bin/install-wifi
sudo chmod +x /usr/bin/install-wifi
```
Then run the following command to identify and download the correct driver. Make sure the 5GHz EDUP adaptor is plugged in:

```bash
sudo install-wifi
```
Run the following lines to add driver support for MediaTek MT7601 based devices (like the unbranded China devices):

```bash
wget http://git.kernel.org/cgit/linux/kernel/git/firmware/linux-firmware.git/plain/mt7601u.bin -O /lib/firmware/mt7601u.bin
```

For other rtl8812au based adaptors, these sites explains how to build drivers on a raspbian system:

[https://www.max2play.com/en/forums/topic/howto-raspberry-pi-3-realtek-802-11ac-rtl8812au/](https://www.max2play.com/en/forums/topic/howto-raspberry-pi-3-realtek-802-11ac-rtl8812au/)
[https://www.raspberrypi.org/forums/viewtopic.php?p=462982](https://www.raspberrypi.org/forums/viewtopic.php?p=462982)

To set the keep alive for the SSHD server:

```bash
sudo nano /etc/ssh/sshd_config
```

Add this line to the end of the file:

```bash
ClientAliveInterval 30
```

## Partition and RAMdisk setup

Setup the RAM disks to reduce SD card I/O and data partition by replacing the /etc/fstab contents with the following:

```bash
proc            /proc           proc    defaults          0       0
/dev/mmcblk0p1  /boot           vfat    defaults,noatime  0       2
/dev/mmcblk0p2  /               ext4    defaults,noatime  0       1
tmpfs           /tmp            tmpfs   defaults,noatime,nosuid,nodev,noexec,mode=1777,size=50M         0       0
tmpfs           /var/tmp        tmpfs   defaults,noatime,nosuid,size=30m 0 0
tmpfs           /var/log        tmpfs   defaults,noatime,nosuid,mode=0755,size=60m 0 0
tmpfs           /var/spool/mqueue tmpfs defaults,noatime,nosuid,mode=0700,gid=12,size=30m 0 0
tmpfs           /home/sonyc/sonycnode/logs tmpfs defaults,noatime,nosuid,mode=0700,size=30m 0 0

# a swapfile is not a swap partition, no line here
#   use  dphys-swapfile swap[on|off]  for that
```

## CPU and audio setup

Add to /etc/rc.local before exit 0 (sets all CPU cores to maximum frequency of 900MHz reducing possible audio input errors)

```
echo performance > /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor
```

Edit /usr/share/alsa/alsa.conf to ensure that USB audio devices are set as the default. Change these lines:

```
defaults.ctl.card 0
```

```
defaults.pcm.card 0
```

to

```
defaults.ctl.card 1
```

```
defaults.pcm.card 1
```
Edit `/usr/share/alsa/alsa.conf` and change the following lines:
```bash
pcm.rear cards.pcm.rear
pcm.center_lfe cards.pcm.center_lfe
pcm.side cards.pcm.side
pcm.hdmi cards.pcm.hdmi
pcm.modem cards.pcm.modem
pcm.phoneline cards.pcm.phoneline
```
to:
```bash
pcm.rear cards.pcm.default
pcm.center_lfe cards.pcm.default
pcm.side cards.pcm.default
pcm.hdmi cards.pcm.default
pcm.modem cards.pcm.default
pcm.phoneline cards.pcm.default
```

## Raspbian setup

Add the following to the /home/sonyc/.bashrc file

```bash
PYTHONPATH=$PYTHONPATH:/home/sonyc/sonynode
PYTHONPATH=$PYTHONPATH:/home/sonyc
```

Set up Keyboard layout to EN-US: 
    
`sudo nano /etc/default/keyboard` and edit `XKBLAYOUT="us"`

Change the timezone to America, New York using the raspi-config "Internationalisation Options" menu:
    
`sudo raspi-config` -> `Internationalisation Options` -> `Change Timezone` -> `America` -> `Eastern`

Enable SSH:
    
`sudo raspi-config` -> `Advanced Options` -> `SSH` -> `Enable`

Set the "Wait for Network at Boot" to "Fast Boot without waiting for network connection" in the raspi-config menu:

`Wait for Network at Boot` -> `Fast Boot without waiting for network connection`


## Package installation and cleanup

Install required packages using apt-get:

```bash
sudo apt-get update
sudo apt-get install htop wavemon stress git python-dev python-pip python-numpy python-scipy portaudio19-dev python-pycurl alsa-utils openvpn
```

Install required packages using pip:

```bash
sudo pip install pyaudio pycrypto tornado supervisor
```

Install Python Audio Tools for handling of different audio file formats:

1. Download source files from [Sourceforge](http://sourceforge.net/projects/audiotools/files/audiotools/2.22/audisotools-2.22.tar.gz/download)
2. Extract and enter the folder. Run: `sudo make install`
3. If above command fails due to some reason, try this: `sudo python setup.py build` then: `sudo python setup.py install`
4. To check if installation was successful: `audiotools-config`

Stop triggerhappy from running on boot:

```bash
sudo update-rc.d -f triggerhappy remove
```

Stop and remove avahi-daemon:

```bash
service avahi-daemon stop
apt-get remove avahi-daemon
```

Clean up any old packages and deb files using the 2 commands below:

```bash
sudo apt-get --purge autoremove
```

```bash
sudo apt-get clean
```
Setup Supervisor daemon to run at system startup:

1. Download the sh file from here: [gist.github.com/Mohitsharma44/ebfb4f690d7c347abb13](https://gist.github.com/Mohitsharma44/ebfb4f690d7c347abb13)
2. Copy the above file to `/etc/init.d/supervisord` _(Supervisord's config file is marked at location /etc/supervisord.conf)_
3. To run it: `sudo chmod +x /etc/init.d/supervisord`
4. To automatically schedule execution: `sudo update-rc.d supervisord defaults`
5. Once the installation is complete, restart the system


## Final pristine image setup stage

Create runonce.sh using `sudo nano /root/runonce.sh` and enter the following:

```bash
#!/bin/sh

```

Create setup.sh using `sudo nano /root/setup.sh` and enter the following:

```bash
#!/bin/sh
(echo p; echo d; echo 2; echo n; echo p; echo 2; echo 131072; echo; echo w; echo q;) | fdisk /dev/mmcblk0
#   p # print the in-memory partition table
#   d # delete the 2nd partition
#   2
#   n # new partition
#   p # primary partition
#   2 # partition number 1
#   122880  # default - start at beginning of disk
# # default, extend partition to end of disk
#   w # write the partition table
#   q # and we're done
# EOF

# Add resize command to runonce.sh script
echo "resize2fs /dev/mmcblk0p2" >> /root/runonce.sh

# Add data mount commands to runonce.sh script
cat <<EOT >> /root/runonce.sh
echo "Creating data partition"
dd if=/dev/zero of=/sonycdata bs=1024 count=12000000
echo "Formatting new partition"
mkfs.ext4 /sonycdata
echo "Updating fstab with mount command"
echo "/sonycdata        /mnt/sonycdata  ext4    loop" >> /etc/fstab
echo "Mounting data partition"
mount /sonycdata /mnt/sonycdata -o loop
echo "Clearing myself and rebooting"
truncate -s 0 /root/runonce.sh
EOT

# Create CSR file and create cert folder structure
NAME="sonyc_nodes"
SSL_DIRECTORY="/etc/ssl/$NAME"


HOSTNAME=$(hostname)
FQDN=$(hostname -f)

FUTURE_CA="$SSL_DIRECTORY/CA.pem"
OUTPUT_CERT="$SSL_DIRECTORY/$NAME.pem"
OUTPUT_KEY="$SSL_DIRECTORY/${NAME}_key.pem"
CONFIG_FILE="$SSL_DIRECTORY/openssl.cnf"

OUTPUT_CSR="/home/sonyc/$HOSTNAME.csr"

#From http://stackoverflow.com/questions/23828413/get-mac-address-using-shell-script
#     http://stackoverflow.com/questions/20752043/print-line-numbers-starting-at-zero-using-awk
#     http://unix.stackexchange.com/questions/171091/remove-lines-based-on-duplicates-within-one-column-without-sort
#     http://unix.stackexchange.com/questions/131217/how-to-remove-duplicate-lines-with-awk-whilst-keeping-empty-lines

MACLIST=$(cat /sys/class/net/*/address | awk '!seen[$0]++ && /.*[1-9].*/  { print "otherName."i++"=macAddress;UTF8:"$0}')

if [ -e "$SSL_DIRECTORY" ] ; then
    echo "$SSL_DIRECTORY already exists."
    exit 1
fi

mkdir "$SSL_DIRECTORY"


cat << EOF > $CONFIG_FILE
#Based on http://stackoverflow.com/questions/21297139/how-do-you-sign-certificate-signing-request-with-your-certification-authority
#         https://www.phildev.net/ssl/opensslconf.html
HOME            = .
RANDFILE        = \$ENV::HOME/.rnd
oid_section	= new_oids

[ new_oids ]
macAddress  = 1.3.6.1.1.1.1.22


####################################################################
[ ca ]
default_ca  = CA_default        # The default ca section

####################################################################
[ req ]
default_bits            = 2048
default_keyfile         = privkey.pem
distinguished_name      = req_distinguished_name
attributes              = req_attributes
string_mask             = nombstr
policy                  = signing_policy
req_extensions          = req_extensions

####################################################################
[ req_distinguished_name ]
countryName                     = Country Name (2 letter code)
countryName_default             = US

stateOrProvinceName             = State or Province Name (full name)
stateOrProvinceName_default     = New York

localityName                    = Locality Name (eg, city)
localityName_default            = Brooklyn

organizationName                = Organization Name (eg, company)
organizationName_default        = New York University

organizationalUnitName          = Organizational Unit (eg, division)
organizationalUnitName_default  = Sounds of New York City

commonName                      = Common Name (e.g. server FQDN or YOUR name)
commonName_default              = $HOSTNAME

emailAddress                    = Email Address
emailAddress_default            = aol@aol.com

####################################################################
[ req_attributes ]

[ req_extensions ]
subjectKeyIdentifier        = hash
nsCertType                  = client
basicConstraints            = CA:FALSE
keyUsage                    = digitalSignature, keyEncipherment
extendedKeyUsage            = clientAuth, macAddress
crlDistributionPoints       = URI:http://control-server.sonyc/crl/$ENV::CRL_NAME
subjectAltName              = @subjectAltName

[ subjectAltName ]
DNS.1=$HOSTNAME
DNS.2=$FQDN
$MACLIST
EOF

openssl req -new -newkey rsa:2048  -nodes -config "$CONFIG_FILE" -sha256 -keyout "$OUTPUT_KEY" -out "$OUTPUT_CSR" -batch

chown sonyc "$OUTPUT_CSR"

echo "Please sign the csr $OUTPUT_CSR and put the cert in file $OUTPUT_CERT"
echo "Please copy the CA to $FUTURE_CA"

# Empty my contents so I do nothing but rc.local doesnt complain on boot
truncate -s 0 /root/setup.sh

reboot

```

This must be done at the end. **This SD card should not be allowed to boot once again after this step.** So, make sure everything is working before doing this. These files automaticaly resize the partitions on the first boot on the SD once flashed.

Edit /etc/rc.local. At the 2nd last line of the file, add (before exit 0):


```bash
# Set hostname of device
FULL_MAC=$(cat /sys/class/net/eth0/address)
MAC=$(echo $FULL_MAC | tr --delete :)

cat <<EOF > /etc/hosts
127.0.0.1  sonycnode-$MAC.sonyc sonycnode-$MAC localhost
::1        localhost ip6-localhost ip6-loopback
ff02::1        ip6-allnodes
ff02::2        ip6-allrouters
10.254.254.254 ingestion-server
10.254.254.253 control-server
EOF

cat <<EOF > /etc/hostname
sonycnode-$MAC
EOF

/etc/init.d/hostname.sh start

hostnamectl set-hostname sonycnode-$MAC

systemctl restart systemd-hostnamed

# Attempt running of setup boot scripts
sh /root/runonce.sh
sh /root/setup.sh
```

Shutdown the machine and take the SD Card out. **DO NOT RESTART OR LET IT BOOT AGAIN.**

## Creating and flashing the pristine image

Insert pristine SD card into a Linux machine. Run df -h to check whether its mounted. If it is, run: (make sure the name matches)

```bash
umount /dev/mmcblk0p1
umount /dev/mmcblk0p2
```

Now, you are ready to create a ghost image out of the OS that was modified. Run (changing the output path to your non root home directory):

```
sudo dd if=/dev/mmcblk0 of=/home/cusp/sonycnode.img bs=1M
chmod 777 /home/cusp/sonycnode.img
```

Note the partition numbers are not used here. Transfer the image created onto a USB stick and plug it into the router or transfer to the flashing Tronsmart array if preferred.

To flash the image file to an SD card, run the following commands:

```bash
sudo dd bs=1M if=sonycnode.img of=/dev/mmcblk0
sync
```