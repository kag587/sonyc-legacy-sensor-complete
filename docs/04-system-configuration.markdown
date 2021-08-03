# <span id="sec:sysconf" label="sec:sysconf">System Configuration</span>

In this Chapter, we discuss the various aspects of the SONYC backend configuration and the DevOps tools behind them. We begin by giving an overview of the various tools used. We then discuss the workflow used to develop and test the system. Finally, we discuss how different components of the SONYC infrastructure are defined. 

## DevOps Tools

DevOps is a methodology for integrating development and operation teams to form an agile pipeline for system changes. Care must be taken when using the term, as it appears that proponents of the method take umbrage for the way it is used in the vernacular. They insist that DevOps is a methodology, not a set of tools. We recommend that SONYC developers continue to use a DevOps inspired methodology to maintain the backend. 

While DevOps is not based on a toolset, there are a number of tools that are closely associated with it. These tools are useful regardless if one maintains a DevOps methodology. In this section, we describe some of those tools. This section is not all-encompassing. We recommend that the reader reviews the standard documentation for each of these tools before utilizing them. 

### Git 
Git is a version control system that is very popular with modern programmers. However, with the advent of DevOps, Git is now is now utilized for server configuration. The test environments, as well as the code to build the main configuration for the SONYC servers, are stored in the [SONYC Test Automation GIT](https://github.com/sonyc-project/SONYC_Test_Automation). 

### Puppet
[Puppet] is a configuration management tool. It is used to define a target configuration and then apply that configuration to a server. Puppet defines *manifests* which define the desired state of the server. These manifests refer to *classes* describing the different aspects of the configuration. These classes divided into modules with common purposes. 

Puppet's syntax can be a bit confusing. It is a domain specific language based on Ruby with a number of idiocentric properties. For example, capitalization has syntactic meaning. At times, a variable must have a prepended dollar sign and, at times, it must not.  Early versions of the language did not support loops or functions leading to strange workarounds. It is strongly recommended that one reads [the language documentation].

SONYC currently utilizes Puppet 10.10. The relevant configurations is stored in the [SONYC_Test_Automation/src/puppet_environments/sonyc/][SONYC environment directory] directory of the [SONYC Test Automation GIT]. The ["manifest" subdirectory] contains the basic definition for each server. The "sonyc" module, located in ["modules/sonyc/" subdirectory], contains most of the configuration details. The rest of the directories in the ["modules" subdirectory] are cloned from the internet and are utilized by the "sonyc" module. 

### Vagrant
[Vagrent] is a tool for automatic provisioning of virtual machines. The SONYC Test Infrastructure utilizes [Vagrant] to provision VMs to replicate the sonyc environment. Once the providers provision a virtual machine,  it automatically calls the relevant puppet script for that server. For usability, a working SONYC environment should be buildable with a single command.

Vagrant has a number of providers that it can configure to host the VMs. The SONYC Test Infrastructure mostly makes use of the VirtualBox and OpenStack providers.  VirtualBox is used for local machines, while OpenStack is utilized to configure the [Brooklyn Research Cluster]. 

## Servers
Please see the section on "SONYC’s systems architecture" for an overview of the different types of servers. Here we give the specifics for both the physical servers as well as the corresponding servers in the test environments. 

The following table summarises the different server types as well as there names in the actual and test environments:

|  Server Type   | Number of Servers |                      Actual DNS                                             |       Test Environment Name            |
|----------------|-------------------|-----------------------------------------------------------------------------|----------------------------------------|
|Ingestion       |2                  |ingestion1-sonyc.engineering.nyu.edu<br>ingestion2-sonyc.engineering.nyu.edu |ingestion-server-1<br>ingestion-server-2|
|Control         |1                  |control-sonyc.engineering.nyu.edu                                            |control-server                          |
|Data Decryption |1                  |decrypt-sonyc.engineering.nyu.edu                                            |data-decryption-server                  |
|Data Access     |1                  |data-sonyc.engineering.nyu.edu                                               |N/A (Use Ingestion Server)              |
|CA              |1                  |N/A (Air Gapped)                                                             |N/A (Simulated Using Scripts)           |

### Ingestion 
The ingestion servers are accessible by SSH from anywhere on the NYU network. They use local user accounts and require an SSH key pair to log in. Most of the configuration for the ingestion server is found inside [ingestion_server.pp] in the SONYC puppet module. 

The heart of the ingestion servers is the sonyc HTTP server code, written in python and cloned from the [sonycserver git]. This server is run using [supervisord] and configured by "/etc/SONYC_server.cnf". The server receives SPL, audio recordings, status updates, and logs and places them in "/var/sonyc/datacache/". In addition, the status updates are sent to ElasticSearch. Five copies of the python service run in tandem on ports 8000 through 8004.

The following puppet code defines this server:

```ruby
    #SONYC Server
    EXEC['install pip'] -> CLASS['supervisord']
    CLASS['python'] ->
    class{ 'supervisord':
      install_pip => false, #pip should already be installed
    } 
    
    #The server config file 
    #$sonic_server_port = 8888
    $sonic_server_upload_data_dir = '/var/sonyc/datacache/'
    $sonic_server_upload_status_dir = '/var/sonyc/datacache/status/'
    $sonic_server_upload_logs_dir = '/var/sonyc/datacache/logs/'   
    $sonic_server_elastic_url = "https://$fqdn:9200"
    $sonic_server_elastic_CA = '/etc/ssl/elasticsearch_api/CA.pem'
    $sonic_server_elastic_cert = '/etc/ssl/elasticsearch_api/elasticsearch_api.pem'
    $sonic_server_elastic_key = '/etc/ssl/elasticsearch_api/elasticsearch_api_key.pem'
    file{ '/etc/SONYC_server.cnf':
        ensure  => file,
        content => template('sonyc/SONYC_server.cnf.erb'),
    }
    
    
    $sonyc_ports = [8000,8001,8002,8003,8004]
    
    $sonyc_ports.each |$sonyc_port| {
    File['/etc/SONYC_server.cnf']~>
        supervisord::program{ "SONYC_server_$sonyc_port":
          command             => "python /home/sonyc/server/server.py --port=$sonyc_port",
          priority            => '100',
          program_environment => {
            'PYTHONPATH'   => '/home/sonyc/server'
          },
          require =>[ EXEC['/bin/bash /etc/init_elasticsearch.sh'],
                      FILE['/var/sonyc/datacache/data'],
                      FILE['/var/sonyc/datacache/status'] 
                    ]
        } 
    }
```
It is important to note that external clients do not connect directly to the python server. Instead, they connect to an [Nginx] proxy, which both validates the client's certificate and route the varius instances of the python code. The proxy is configured as folows

```ruby

    class{'sonyc::elasticsearch' :
        local_elasticsearch_host => $local_elasticsearch_host,
        elasticsearch_hosts => $elasticsearch_hosts
    }

 #ngix
    class{ 'nginx::config': } 
    class{ 'nginx': } 


    CLASS['nginx::package'] -> 
    nginx::resource::upstream { 'backends':
      members => $sonyc_ports.map |$sonyc_port| {"127.0.0.1:$sonyc_port"}
    } 
    
    
    CLASS['nginx::package'] -> 
    nginx::resource::vhost { 'sonyc-localhost':
        ssl => true,
        listen_port => 443,
        ssl_cert  => '/etc/ssl/sonyc_nodes/sonyc_nodes.pem',
        ssl_key   => '/etc/ssl/sonyc_nodes/sonyc_nodes_key.pem',
        ssl_client_cert => '/etc/ssl/sonyc_nodes/CA.pem',
        ssl_crl => '/etc/ssl/sonyc_nodes/sonyc_nodes.crl',
        ssl_protocols => 'TLSv1 TLSv1.1 TLSv1.2',
        ssl_ciphers => $sonyc::ngix_ciphers,
        ssl_session_timeout => '1d',
        ssl_session_tickets => 'off',

        
        use_default_location => false, 
        access_log => '/var/log/nginx/sonyc.access_log',
        error_log => '/var/log/nginx/sonyc.error_log',
        

        
        subscribe => [ SONYC::SSL_REQUEST['sonyc_nodes'] ]
    } 
    CLASS['nginx::package'] -> 
    nginx::resource::location{ 'sonyc-localhost-root':
        vhost => 'sonyc-localhost',
        ssl_only => true,
        location  => '/',
        #www_root => '/home/sonyc/production_server',
        proxy_pass_header => ['Server'],
        proxy_set_header => [
            'Host $http_host',
            'X-Real-IP $remote_addr',
            'X-Scheme $scheme',
            'X-Client-Cert $ssl_client_cert',
            'X-Client-SDN $ssl_client_s_dn'
            ],
        proxy => 'http://backends',
    }

    CLASS['nginx::package'] -> 
    file{ '/etc/nginx/conf.d/default.conf' : 
        ensure => absent,
        notify => Class['::nginx::service']
    }
```

Once the file is copied to the data cache, it needs to be moved to the backend storage which is mounted at ```$output_mount_point``` or '/mount/vida-sonyc/' on both the production environment and the test environment.  [move_finished_files.sh] is responsible for moving the files. The script is designed to make sure it only moves the files when they have been uploaded and closed and when the output directory is properly mounted. It uses the Linux "mv" command which will nor delete a file if it fails to copy, ensuring no lost data. [move_finished_files.sh] automatically starts subprocesses to move the files in parallel. The maximum number of process is its third argument. 

There is currently a bug where, if the storage directory is not mounted, [move_finished_files.sh] will busy wait unit it is. This drains a lot of system resources. 

[move_finished_files.sh] is run by [supervisord] as defined in the following:

```ruby

    File['/var/sonyc'] ->
    file{ '/var/sonyc/move_finished_files.sh': 
        ensure  => 'file',
        mode                => 'a+x',
        source => 'puppet:///modules/sonyc/move_finished_files.sh',
    }
    
supervisord::program{ "move_data":
      command             => "/bin/bash /var/sonyc/move_finished_files.sh /var/sonyc/datacache $output_mount_point 100",
      priority            => '100',
      subscribe =>[ 
                  FILE['/var/sonyc/move_finished_files.sh']
                ]
    } 
```

Unfortunately, our storage backend runs out of inodes if too many small files are stored in it. As a solution, the ingestion servers compress each of the date directories once it has been untouched for a period of time. This is done by the [archive_files.sh] script, which in turn calls [archive_one_folder.sh]. 

[archive_files.sh] searches for folders that have not been modified for more than a day. When it finds such a file, it locks it in a manner that works over NSF shares, and calls [archive_one_folder.sh]. The goal of the locking is to prevent more than one ingestion server from archiving the same folder at the same time. However, in the worst-case scenario, two copies of the archive will be created.  Additionally, the order of the files being compressed is permuted randomly to decrease the likelihood of multiple ingestion servers trying to archive the same folder at the same time. 

[archive_one_folder.sh] was carefully written to ensure that no data is ever lost, even if power or networking goes down in mid-transfer. First, all the files in the directory to be archived are copied to a local temp directory on the ingestion server. The temp directory is achieved and copied to the shared storage, taking care not to override any existing archive. The archive is then decompressed from the shared storage to a new temp directory on the ingestion server. The files in the temp directory are compared byte by byte to the version in the original folder. If, and only if, the files match, the original file is deleted. Finally, the folder is empty it is deleted. Note that this process will not delete a file if it is changed after archiving, nor will it delete a folder if a new file is placed in it in mid-process and is missing in the archive. 

A separate instance of  [archive_one_folder.sh] is run for each of the data, status, audio, SPL, test audio, test SPL, and logs directory. This allows for multiple comparisons to take place at the same time. If the current script gets overwhelmed, it should be safe to start additional copies of it. 

The Puppet code that provisions these scripts is as follows:
```ruby

    File['/var/sonyc'] ->
    file{ '/var/sonyc/archive_files.sh': 
        ensure  => 'file',
        mode                => 'a+x',
        source => 'puppet:///modules/sonyc/archive_files.sh',
    }
    
    File['/var/sonyc'] ->
    file{ '/var/sonyc/archive_one_folder.sh': 
        ensure  => 'file',
        mode                => 'a+x',
        source => 'puppet:///modules/sonyc/archive_one_folder.sh',
    }
    
 supervisord::program{ "archive_status_files":
      command             => "/bin/bash /var/sonyc/archive_files.sh $output_mount_point/status",
      priority            => '100',
      subscribe =>[ 
                  FILE['/var/sonyc/archive_files.sh'],
                  FILE['/var/sonyc/archive_one_folder.sh']
                ]
    } 

    supervisord::program{ "archive_audio_files":
      command             => "/bin/bash /var/sonyc/archive_files.sh $output_mount_point/audio",
      priority            => '101',
      subscribe =>[ 
                  FILE['/var/sonyc/archive_files.sh'],
                  FILE['/var/sonyc/archive_one_folder.sh']
                ]
    } 
    
    supervisord::program{ "archive_spl_files":
      command             => "/bin/bash /var/sonyc/archive_files.sh $output_mount_point/spl",
      priority            => '102',
      subscribe =>[ 
                  FILE['/var/sonyc/archive_files.sh'],
                  FILE['/var/sonyc/archive_one_folder.sh']
                ]
    } 
    

    supervisord::program{ "archive_test_audio_files":
      command             => "/bin/bash /var/sonyc/archive_files.sh $output_mount_point/test/audio",
      priority            => '101',
      subscribe =>[ 
                  FILE['/var/sonyc/archive_files.sh'],
                  FILE['/var/sonyc/archive_one_folder.sh']
                ]
    } 
    
    supervisord::program{ "archive_test_spl_files":
      command             => "/bin/bash /var/sonyc/archive_files.sh $output_mount_point/test/spl",
      priority            => '102',
      subscribe =>[ 
                  FILE['/var/sonyc/archive_files.sh'],
                  FILE['/var/sonyc/archive_one_folder.sh']
                ]
    } 
    
    supervisord::program{ "archive_logs_files":
      command             => "/bin/bash /var/sonyc/archive_files.sh $output_mount_point/logs",
      priority            => '103',
      subscribe =>[ 
                  FILE['/var/sonyc/archive_files.sh'],
                  FILE['/var/sonyc/archive_one_folder.sh']
                ]
    }     

```
In addition to ingesting data, the ingestion servers also provide two OpenVPN services. The first of these, the 'ingestion-server' OpenVPN service allows clients to connect to the ingestion server. The second, the 'ingestion-server-control' OpenVPN service allows the control server to securely connect to the ingestion servers. 

Each ingestion server has its own address space which it assigns to clients or servers. The separate address spaces allow the different ingestion servers to work independently of one another. Additionally, the regular and control OpenVPN services have their own address spaces allowing the ingestion server to know where packets originate from. 

The following table shows the address spaces used:

|  Server  |Regular OpenVPN|Control OpenVPN|   Server VPN IPs    |
|----------|:-------------:|:-------------:|:-------------------:|
|ingestion1|10.8.0.0/24    |10.8.0.128/24  |10.8.0.1 & 10.8.128.1|
|ingestion2|10.9.0.0/24    |10.9.0.128/24  |10.9.0.1 & 10.9.128.1|

These are defined in the ["manifest" subdirectory] of the [SONYC environment directory] ([default.pp] for the Vagrant environment or [actual.pp] for the live environment) as the ```$openvpn_server_index``` parameters of the ```sonyc::ingestion_server``` class. 

The regular OpenVPN and control OpenVPN address spaces are bridged together using iptables. This allows the control server to communicate with the nodes and the nodes to communicate with the control server. Currently, this is used to allow the control server to SSH into the nodes. However, in the future, it can also be used to allow the nodes to update themselves from the control server. 

OpenVPN pushes a routing rule to route 10.254.254.0/24 over the VPN tunnel. The iptable rules translate 10.254.254.254 to be the current ingestion server. As such, clients that are connected to the VPN can directly to the correct ingestion server using 10.254.254.254. The hosts file on the nodes gives that ip address the name "ingestion-server". 

When a sensor connects to the VPN, OpenVPN assigns it an arbitrary IP address. To keep track of the mapping of IP addresses to connected, OpenVPN is configured to call [learn-address.sh] whenever a node connects or disconnects. This script updates ```/etc/hosts.openvpn-clients``` and reloads dnsmasq (see below). 

The configuration for OpenVPN, along with the relevant iptable rules are below:
```ruby

    class{ 'openvpn':
     autostart_all => true,
    } 
    
    openssl::dhparam{ "/etc/ssl/dhparam-openssl.pem":
	  ensure => 'present',
	  size   => 2048,
	  path => "/etc/ssl/dhparam-openssl.pem"
	}

    #Used in the sonyc/learn-address.sh.erb template
    $vpn_hosts_file_name = '/etc/hosts.openvpn-clients'
    $vpn_domain_name = 'sonyc'
   File['/etc/learn-address.sh']->
    openvpn::server{ 'ingestion-server':
      common_name => '$hostname',
      server       => "10.$openvpn_server_index.0.0 255.255.128.0",
      extca_enabled => true,
      extca_ca_cert_file => '/etc/ssl/sonyc_nodes/CA.pem',
      crl_verify => true,
      extca_ca_crl_file => '/etc/ssl/sonyc_nodes/sonyc_nodes.crl',
      extca_server_cert_file => '/etc/ssl/sonyc_nodes/sonyc_nodes.pem',
      extca_server_key_file => '/etc/ssl/sonyc_nodes/sonyc_nodes_key.pem',  
      extca_dh_file => '/etc/ssl/dhparam-openssl.pem',
      local => $ip_addr_to_use,
      user => 'root',
      logfile => '/var/log/openvpn-ingestion-server',
      proto => 'udp',
      dev =>  'tun0',
      topology => 'p2p',
      push => ["route 10.$openvpn_server_index.128.0 255.255.128.0",
               "route 10.254.254.0  255.255.255.0",
               "topology p2p"],
      custom_options => {
        'learn-address' => '/etc/learn-address.sh',
        'auth'   => 'SHA256',
        'keepalive' => '10 120'
      },
      cipher => 'AES-128-CBC',
      
      
      subscribe => [ SONYC::SSL_REQUEST['sonyc_nodes'],
                     OPENSSL::DHPARAM["/etc/ssl/dhparam-openssl.pem"] ]
    } 
    
    sonyc::ssl_request{ 'control_vpn':
        sign_cert_extra_terms => 'signing_server'
    }
    
    File['/etc/learn-address.sh']->
    openvpn::server{ 'ingestion-server-control':
      common_name => '$hostname',
      port         => 1195,
      server       => "10.$openvpn_server_index.128.0 255.255.128.0",
      extca_enabled => true,
      extca_ca_cert_file => '/etc/ssl/control_vpn/CA.pem',
      crl_verify => true,
      extca_ca_crl_file => '/etc/ssl/control_vpn/control_vpn.crl',
      extca_server_cert_file => '/etc/ssl/control_vpn/control_vpn.pem',
      extca_server_key_file => '/etc/ssl/control_vpn/control_vpn_key.pem',  
      extca_dh_file => '/etc/ssl/dhparam-openssl.pem',
      local => $backend_fqdn,
      user => 'root',
      logfile => '/var/log/openvpn-ingestion-server-control',
      proto => 'udp',
      dev =>  'tun1',
      topology => 'p2p',
      push => ["route 10.$openvpn_server_index.0.0 255.255.128.0",
               "topology p2p"],
      custom_options => {
        'learn-address' => '/etc/learn-address.sh',
        'auth'   => 'SHA256',
        'keepalive' => '10 120'
      },
      cipher => 'AES-128-CBC',
      subscribe => [ SONYC::SSL_REQUEST['control_vpn'],
                     OPENSSL::DHPARAM["/etc/ssl/dhparam-openssl.pem"] ]
    }    

 #Block vpn tunnal trafic from the wrong device
        firewall { '005 reject spoofed tun0 trafic':
            chain     => "INPUT",
            proto  => 'all',
            iniface => '! tun0',
            action => 'reject',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            before => [],
         }

         firewall { '006 reject spoofed tun1 trafic':
            chain     => "INPUT",
            proto  => 'all',
            iniface => '! tun1',
            action => 'reject',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            before => [],
         }        

  #Connect the two tunnels (if it is from the correct device) 
        firewall { '011 reject spoofed tun0 trafic':
            chain     => "FORWARD",
            proto  => 'all',
            iniface => '! tun0',
            action => 'reject',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            before => [],
         }

         firewall { '012 reject spoofed tun1 trafic':
            chain     => "FORWARD",
            proto  => 'all',
            iniface => '! tun1',
            action => 'reject',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            before => [],
         }   
         
        #http://serverfault.com/questions/431593/iptables-forwarding-between-two-interface
        firewall { '013 fowared tun1 to tun0':
            chain     => "FORWARD",
            physdev_in => 'tun1',
            iniface => 'tun1',
            outiface => 'tun0',            
            proto  => 'all',
            action => 'accept',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            dst_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
        }
        
        firewall { '014 fowared tun0 to tun1':
            chain     => "FORWARD",
            physdev_in => 'tun0',
            iniface => 'tun0',
            outiface => 'tun1',            
            proto  => 'all',
            action => 'accept',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            dst_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
        }      

        firewall { '015 nat tun0':
           table    => 'nat',
           chain    => 'POSTROUTING',
           jump     => 'MASQUERADE',
           proto     => 'all',
           physdev_out => 'tun0',
        }


        firewall { '016 nat tun1':
           table    => 'nat',
           chain    => 'POSTROUTING',
           jump     => 'MASQUERADE',
           proto     => 'all',
           physdev_out => 'tun1',
        }
        
        #nat 10.254.254.254 to the current server
        firewall { '017 tun0 nat 10.254.254.254':
           table    => 'nat',
           chain    => 'PREROUTING',
           jump     => 'DNAT',
           iniface => 'tun0',
           proto     => 'all',
           destination => '10.254.254.254',
           todest => "10.$openvpn_server_index.0.1" 
        }
```

As a convenience for the administrators, each ingestion server runs dnsmasq, a DNS server. dnsmasq reads ```/etc/hosts.openvpn-clients```, which keeps track of the IP addresses assigned to nodes. As noted above, [learn-address.sh] updates ```/etc/hosts.openvpn-clients```  whenever a node connects or disconnects. It also refreshes dnsmasq by calling ```/etc/reload_dnsmasq```. 

dnsmasq is defined by the following puppet code:
```ruby
    #Used in the sonyc/learn-address.sh.erb template
    $vpn_hosts_file_name = '/etc/hosts.openvpn-clients'
    $vpn_domain_name = 'sonyc'


    class{ 'dnsmasq':
      expand_hosts      => true,
      enable_tftp       => false,
      domain_needed     => true,
      bogus_priv        => true,
      no_negcache       => true,
      no_hosts          => true,
      cache_size        => 1000,
      restart           => true,
      config_hash       => {
        addn-hosts  => $vpn_hosts_file_name,
        no-resolv => true,
        #local => true
      }
    }
    #dnsmasq
    file{ '/etc/default/dnsmasq': 
        ensure  => 'file',
        source => 'puppet:///modules/sonyc/dnsmasq.default',
        notify => Service[ 'dnsmasq' ]
    } 
```

Status updates are stored on a distributed [ElasticSearch] database. This database is the only component that requires direct coordination between ingestion servers. We currently use version 5.01. This is a security hole, and it should be updated.

Since, at the time of building the servers, "ElasticSearch X-Pack" required a commercial license, we use the 3ed party [Search Guard] to provide encryption and certificate authentication. Now that ElasticSearch has open source support for https, it may make sense to switch to that in the future. 

ElasticSearch makes use of two SSL certificate types. The first, "elasticsearch_nodes" is used to authenticate the nodes in the  ElasticSearch cluster. The second, "elasticsearch_api" is used clients connecting to ElasticSearch's REST API. 

ElasticSearch runs on top of the JVM. A peculiarity of this setup means that  ElasticSearch needs to allocate all of its memory at startup. This is configured by the  ```$elastic_search_memory``` variable in [elasticsearch.pp]. For the ingestion servers, this is set at 5 gigabytes (512 megabytes in the vagrant environment). It should be noted that, at times, multiple instances of ElasticSearch must run at the same time. As such, this variable cannot be more than half the memory of the node and should be less than a third of the total memory.  

The initial schema for the ElasticSearch database is built by the  [init_elasticsearch.sh] script. Afterward, ElasticSearch updates the schema on its own. However, at times, the automatically updated schema gives undesirable types. In those situations, the schema needs to be updated manually. 

The code that defines the ElasticSearch definition is defined below. It should be noted that we use a custom class to share the same definition between the ingestion servers and the control server. It is important to note that the ```$master_only``` is false for the ingestion server. The class is defined in [elasticsearch.pp]. 


```ruby
    class{'sonyc::elasticsearch' :
        local_elasticsearch_host => $local_elasticsearch_host,
        elasticsearch_hosts => $elasticsearch_hosts
    }

    CLASS['python'] ->
    elasticsearch::python{ 'rawes': }

class sonyc::elasticsearch(
    $local_elasticsearch_host,
    $elasticsearch_hosts,
    $master_only = false
)
{

    if $master_only
    {
        $node_master = true
        $node_data   = false
        $node_ingest = true
    }
    else
    {
        $node_master = true
        $node_data   = true
        $node_ingest = true
    }

    #Elastic Search
    class{ 'java8':
#      version => '8',
#      distribution => 'jre',
    } ->
    class{ 'elasticsearch':
      java_install => false,
      manage_repo  => false,
      repo_version => '5.x',
      #version => '5.0.1',
      package_url => 'https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-5.0.1.deb',
      restart_on_change => true,
      config => { 
        'network.host' => ['_local_', "$fqdn" , "$local_elasticsearch_host"],
        'cluster.name' => 'ingestion-server',
        'discovery.zen.ping.unicast.hosts' => $elasticsearch_hosts,
        'discovery.zen.minimum_master_nodes' => 2,
        'discovery.zen.commit_timeout' => '1s',
        'action.auto_create_index' => 'false',
        
        'node.master' => $node_master,
        'node.data'   => $node_data,
        'node.ingest' => $node_ingest,
        
        'searchguard.ssl.transport.truststore_filepath' => 'truststore_nodes.jks',
        'searchguard.ssl.transport.keystore_password' => 'acd0c2a3f4052d493c748029c0712c64',
        'searchguard.ssl.transport.keystore_filepath' => 'keystore_nodes.jks',
        'searchguard.ssl.transport.truststore_password' => 'acd0c2a3f4052d493c748029c0712c64',
        'searchguard.ssl.transport.enforce_hostname_verification' => true,
        
        'searchguard.ssl.http.truststore_filepath' => 'truststore_api.jks',
        'searchguard.ssl.http.keystore_password' => 'acd0c2a3f4052d493c748029c0712c64',
        'searchguard.ssl.http.keystore_filepath' => 'keystore_api.jks',
        'searchguard.ssl.http.truststore_password' => 'acd0c2a3f4052d493c748029c0712c64',
        'searchguard.ssl.http.enabled' => true,
        
        'searchguard.ssl.http.clientauth_mode' => 'REQUIRE'
      }
    }
    elasticsearch::instance{ 'es-01': }

    #Create the keys for elasticsearth
    sonyc::ssl_request{ 'elasticsearch_nodes':
        sign_cert_extra_terms => 'signing_client_server'
    } 
    
    File['/etc/elasticsearch/es-01'] ->
    java_ks{ 'root-ca-chain-node-0':
      ensure       => latest,
      certificate  => '/etc/ssl/elasticsearch_nodes/CA.pem',
      target       => '/etc/elasticsearch/es-01/truststore_nodes.jks',
      trustcacerts => true,
      password => 'acd0c2a3f4052d493c748029c0712c64',
      notify => Elasticsearch::Service['es-01'],
      
      subscribe => [ SONYC::SSL_REQUEST['elasticsearch_nodes'] ] 
    }
    
    
    File['/etc/elasticsearch/es-01'] ->
    java_ks{ 'elasticsearch:keystore-node':
      ensure       => latest,
      certificate  => '/etc/ssl/elasticsearch_nodes/elasticsearch_nodes.pem',
      private_key => '/etc/ssl/elasticsearch_nodes/elasticsearch_nodes_key.pem',
      target       => '/etc/elasticsearch/es-01/keystore_nodes.jks',
      password => 'acd0c2a3f4052d493c748029c0712c64',
      notify => Elasticsearch::Service['es-01'],
      
      subscribe => [SONYC::SSL_REQUEST['elasticsearch_nodes'] ] 
    }
    
    sonyc::ssl_request{ 'elasticsearch_api':
        sign_cert_extra_terms => 'signing_client_server'
    }  
    
    File['/etc/elasticsearch/es-01'] ->
    java_ks{ 'root-ca-chain-api-0':
      ensure       => latest,
      certificate  => '/etc/ssl/elasticsearch_api/CA.pem',
      target       => '/etc/elasticsearch/es-01/truststore_api.jks',
      trustcacerts => true,
      password => 'acd0c2a3f4052d493c748029c0712c64',
      notify => Elasticsearch::Service['es-01'],
      
      subscribe => [ SONYC::SSL_REQUEST['elasticsearch_api'] ] 
    } 

    File['/etc/elasticsearch/es-01'] ->
    java_ks{ 'elasticsearch:keystore-api':
      ensure       => latest,
      certificate  => '/etc/ssl/elasticsearch_api/elasticsearch_api.pem',
      private_key => '/etc/ssl/elasticsearch_api/elasticsearch_api_key.pem',
      target       => '/etc/elasticsearch/es-01/keystore_api.jks',
      password => 'acd0c2a3f4052d493c748029c0712c64',
      notify => Elasticsearch::Service['es-01'],
      
      subscribe => [SONYC::SSL_REQUEST['elasticsearch_api'] ] 
    }
    if $::is_vagrant 
    {
        $elastic_search_memory = '512m'
    } 
    else 
    {
        if $master_only 
        {
            $elastic_search_memory = '1g'
        } 
        else 
        {
            $elastic_search_memory = '5g'       
        }
    }
    Class[ 'elasticsearch::package' ] ->
    file{ '/etc/elasticsearch/jvm.options':
        ensure =>  file,
        content => template('sonyc/jvm.options.erb'),
    } ~> Elasticsearch::Service['es-01']
    
    
    
    $search_guard_vertion = '5.0.1-17' 

    Class['elasticsearch'] ->
    elasticsearch::plugin {"com.floragunn:search-guard-ssl:$search_guard_vertion" : 
         instances => 'es-01',
         module_dir => 'search-guard-ssl'
    }
    
    ELASTICSEARCH::INSTANCE['es-01'] ->
    file{ '/etc/init_elasticsearch.sh':
        ensure =>  file,
        content => template("sonyc/init_elasticsearch.sh.erb")
    } ->
    exec{ '/bin/bash /etc/init_elasticsearch.sh' :
    }
}

```


The ingestion server uses [fluentd] and its [dstat] plugin to keep track of various statistics. These statistics include CPU usage, disk IO, and network IO. fluentd then forwards this data to the ElasticSearch database where it is stored in the 'server-status' index. The Puppet code that defines this feature is below:

```ruby
    #fluentd
    include fluentd

    fluentd::plugin { 'fluent-plugin-elasticsearch': }
    fluentd::plugin { 'fluent-plugin-dstat': }
    
    package{'dstat':} ->
    fluentd::config { '500_elasticsearch.conf':
      config => {
        'source' => [
          {
            'type' => 'dstat',
            'tag' => 'input.dstat',
            'option' => '-af',
          },
          {
            'type' => 'dstat',
            'tag' => 'input.dstat-full',
            'option' => '-a',
            'tmp_file' => "/tmp/fluent-plugin-dstat-full.fifo"
          }         
        ],
        'filter' => [
            {
                'tag_pattern'     => '**',
                'type'            => 'record_transformer',
                'enable_ruby' => true,
                'record' => {
                    'time' => '${time.strftime(\'%Y-%m-%dT%H:%M:%S%z\')}',
                    'tag' => '${tag}'
                }
            }
        ],
        'match'  => {
          'tag_pattern'     => '**',
          'type'            => 'elasticsearch',
          'hosts'           => "https://$local_elasticsearch_host:9200/",
          'index_name'      => 'server-status',
          'type_name'       => 'server-status-type',
          'logstash_format' => false,
          'reconnect_on_error' => true,
          'flatten_hashes' => true,
          'ca_file' => '/etc/ssl/elasticsearch_api/CA.pem',
          'client_cert'  => '/etc/ssl/elasticsearch_api/elasticsearch_api.pem',
          'client_key' => '/etc/ssl/elasticsearch_api/elasticsearch_api_key.pem',
          
          subscribe => [SONYC::SSL_REQUEST['elasticsearch_api'] ] 

        }
      }
    }
``` 



There are a number of open ports on the ingestion servers that are needed to function. These are defined using iptables, in addition to the rules listed above to allow OpenVPN to function. The following table summarises all the iptables rules (all ports are TCP unless otherwise noted): 

|    port   |          rule name        |            usage            |                                 notes                            |
|-----------|---------------------------|-----------------------------|------------------------------------------------------------------|
|All        |000 Let vagrant connect    |vagrant ssh or other access  |only on test environment and only for eth0 (connection to host)   |
|icmp       |007 accept all icmp        |allow icmp packets           |Allow ping and other icmp packets                                 |
|22         |020 allow ssl access       |Allow SSH access to server   |                                                                  |
|1194 & 1195|021 allow OpenVPN access   |OpenVPN client connections   |                                                                  |
|9200 & 9300|022 Allow Elasticsearch    |Elasticsearch cluster and api|                                                                  |
|53 (tcp)   |023 Allow DNS: tcp         |DNS name resolution          |Only open over the OpenVPN connection.                            |
|53 (udp)   |023 Allow DNS: udp         |DNS name resolution          |Only open over the OpenVPN connection.                            |
|443        |522 Allow https from client|REST API                     |Open to outside of NYU network (configured via NYU firewall by IT)|  

For reference, here is the full iptable configuration for the ingestion servers:
```ruby
    #Firewall
    sysctl{ 'net.ipv4.ip_forward': value => '1' }
    sysctl{ 'net.ipv6.conf.all.disable_ipv6': value => '1' }
    sysctl{ 'net.ipv6.conf.default.disable_ipv6': value => '1' }
    
    resources{ 'firewall':
      purge => true,
    }

        
    class ingestion_server_fw_pre {
        Firewall {
            require => undef,
        }
        #If we are running from vagrant, make sure we don't lock ourselvs out
        if $is_vagrant {
          firewall { '000 Let vagrant connect':
            chain     => "INPUT",
            iniface => 'eth0',
            proto  => 'all',
            action => 'accept',
            before => [],
          }    
   
        }
          firewall { '001 accept established connections':
            chain     => "INPUT",
            proto  => 'all',
            state  => ['RELATED', 'ESTABLISHED'],
            action => 'accept',
            before => [],
          }     
          
          firewall { '002 accept established connections':
            chain     => "OUTPUT",
            proto  => 'all',
            state  => ['RELATED', 'ESTABLISHED'],
            action => 'accept',
            before => [],
          }  

         firewall { '002 accept loopback':
            chain     => "INPUT",
            proto  => 'all',
            iniface => 'lo',
            action => 'accept',
            before => [],
         }           
         
         firewall { '003 accept loopback':
            chain     => "OUTPUT",
            proto  => 'all',
            outiface => 'lo',
            action => 'accept',
            before => [],
         }

        #Block vpn tunnal trafic from the wrong device
        firewall { '005 reject spoofed tun0 trafic':
            chain     => "INPUT",
            proto  => 'all',
            iniface => '! tun0',
            action => 'reject',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            before => [],
         }

         firewall { '006 reject spoofed tun1 trafic':
            chain     => "INPUT",
            proto  => 'all',
            iniface => '! tun1',
            action => 'reject',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            before => [],
         }        
         
         #Allow ICPM
         firewall { '007 accept all icmp':
            proto  => 'icmp',
            action => 'accept',
         }   
         
         
        #Connect the two tunnels (if it is from the correct device) 
        firewall { '011 reject spoofed tun0 trafic':
            chain     => "FORWARD",
            proto  => 'all',
            iniface => '! tun0',
            action => 'reject',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            before => [],
         }

         firewall { '012 reject spoofed tun1 trafic':
            chain     => "FORWARD",
            proto  => 'all',
            iniface => '! tun1',
            action => 'reject',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            before => [],
         }   
         
        #http://serverfault.com/questions/431593/iptables-forwarding-between-two-interface
        firewall { '013 fowared tun1 to tun0':
            chain     => "FORWARD",
            physdev_in => 'tun1',
            iniface => 'tun1',
            outiface => 'tun0',            
            proto  => 'all',
            action => 'accept',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            dst_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
        }
        
        firewall { '014 fowared tun0 to tun1':
            chain     => "FORWARD",
            physdev_in => 'tun0',
            iniface => 'tun0',
            outiface => 'tun1',            
            proto  => 'all',
            action => 'accept',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            dst_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
        }      

        firewall { '015 nat tun0':
           table    => 'nat',
           chain    => 'POSTROUTING',
           jump     => 'MASQUERADE',
           proto     => 'all',
           physdev_out => 'tun0',
        }


        firewall { '016 nat tun1':
           table    => 'nat',
           chain    => 'POSTROUTING',
           jump     => 'MASQUERADE',
           proto     => 'all',
           physdev_out => 'tun1',
        }
        
        #nat 10.254.254.254 to the current server
        firewall { '017 tun0 nat 10.254.254.254':
           table    => 'nat',
           chain    => 'PREROUTING',
           jump     => 'DNAT',
           iniface => 'tun0',
           proto     => 'all',
           destination => '10.254.254.254',
           todest => "10.$openvpn_server_index.0.1" 
        }

        #allow incoming ssh and openvpn connections, regardless of where they are from
        firewall { '020 allow ssl access':
            chain     => "INPUT",
            dport   => [22],
            proto  => tcp,
            action => accept,
        }
        
         firewall { '021 allow OpenVPN access':
            chain     => "INPUT",
            dport   => [1194, 1195],
            proto  => udp,
            action => accept,
        }       
        

        firewall { '022 Allow Elasticsearch':
            chain     => "INPUT",
            dport   => [9200,9300],
            proto  => tcp,
            action => accept,
        }
        #Allow DNS over the tunnals
        firewall { '023 Allow DNS: tcp':
            chain     => "INPUT",
            dport   => [53],
            proto  => 'tcp',
            action => accept,
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.255.255",
        }

        firewall { '023 Allow DNS: udp':
            chain     => "INPUT",
            dport   => [53],
            proto  => 'udp',
            action => accept,
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.255.255",
        }
        
         firewall { '522 Allow https from client':
            chain     => "INPUT",
            dport   => [443],
            proto  => tcp,
            action => accept,
        }       
        
    }

    class ingestion_server_fw_post {
        firewallchain { 'INPUT:filter:IPv4':
          policy => 'drop',
          before => [],
        }  ->
        firewallchain { 'INPUT:filter:IPv6':
          policy => 'drop',
          before => [],
        } ->
        firewallchain { 'OUTPUT:filter:IPv6':
          policy => 'drop',
          before => [],
        }  
    } 
    
    Firewall {
      require => Class['sonyc::ingestion_server::ingestion_server_fw_pre'],
      before  => Class['sonyc::ingestion_server::ingestion_server_fw_post'],
    }

    class{ ['sonyc::ingestion_server::ingestion_server_fw_pre', 'sonyc::ingestion_server::ingestion_server_fw_post']: }

    
    class { 'firewall': }
```

### Control 
The control server is accessible by SSH from anywhere on the NYU network. They use local user accounts and require an SSH key pair to log in.  Most of the configuration for the control is found inside [control_server.pp] in the SONYC puppet module. 

The primary purpose of the control server is to provide a central place for the instrumentation team to access all of the nodes. This is accomplished through two components: OpenVPN connections allowing the team to ssh into the nodes through any ingestion server and a [PowerDNS Recursor] that amalgamates all the DNS records of the various ingestion servers. The combination of the two allows users to simply SSH into the domain name of the node, regardless of which ingestion server it is connected to.

The control server runs an OpenVPN client for each ingestion server, connecting to that ingestion server's control VPN; authenticating using a "control_vpn" client certificate. The connection is established using UDP port 1195 using "AES-128-CBC" for security and authenticating with "SHA256". 

The full configuration is given by the following code. It was developed using an old version of puppet that did not yet support loops. As such, it uses a workaround making use of inline ruby templates. This can be updated in the future. 

```ruby

    #VPN connections
    sonyc::ssl_request { 'control_vpn':
        sign_cert_extra_terms => 'signing_client'
    }
    
    SONYC::SSL_REQUEST['control_vpn'] ~> OPENVPN_CLIENT::CLIENT<| |>
    
    $openvpn_client_defualts = {
      dev => 'tun',
      port => 1195,
      proto => 'udp',
      nobind => true,
      comp_lzo => " ",
      user => 'root',
      ca => "/etc/ssl/control_vpn/CA.pem",
      cert => "/etc/ssl/control_vpn/control_vpn.pem",
      key => "/etc/ssl/control_vpn/control_vpn_key.pem",
      cipher => 'AES-128-CBC',
      auth => 'SHA256',
      remote_cert_tls => 'server',
      
      subscribe => [ SONYC::SSL_REQUEST['control_vpn'] ]
    }
    
    
    
    $openvpn_client_list_ruby = '<%= 
        Hash[@vpn_server_list.map do |server_name,server_info|
            [server_name,
                {
                    "custom_options" => ["remote-random", "log-append /var/log/openvpn-#{server_name}"] ,
                    "server" => server_info["server_dns_name"],
                } 
            ]
        end].to_json
    %>'
    $openvpn_client_list = parsejson( inline_template($openvpn_client_list_ruby) ) 
    
    create_resources('openvpn_client::client',$openvpn_client_list,$openvpn_client_defualts)
```

 [PowerDNS Recursor] relays DNS queries to other nameservers. The control server uses a PowerDNS Recursor to relay DNS requests to the proper DNS server. Requests to domain names with the ".sonyc" top-level domain are sent to each of the authoritative DNS servers on each of the ingestion servers.  Other requests are sent to the normal DNS servers, as defined in [default.pp] for the test environment or [actual.pp] for the live environment.

There is a slight difference between the DNS server on the test environment and the production environment. On the production environment, the DNS server only listens to the loopback device. In the Vagrant environment, it is open to requests from any source. 

The configuration source is below. Like the OpenVPN server, the code was initially written for a version of Puppet that did not support iterations. As such, the code uses a workaround with inline ruby templates. This can now be updated to use Puppet's native iterations.
```ruby
 $openvpn_dns_list_ruby = '<%= 
        @vpn_server_list.map do |server_name,server_info|
             "10.#{server_info[\'server_index\']}.0.1"   
        end.join(";")
    %>'
    $openvpn_dns_list = inline_template($openvpn_dns_list_ruby)
    
    
    if $::is_vagrant {
        $dns_listen_range = '0.0.0.0/0'  
        $dns_listen_local = '0.0.0.0'
    } else {
        $dns_listen_range = '127.0.0.1' 
        $dns_listen_local = '127.0.0.1'
    }
    class{ 'powerdns':
        authoritative => false,
        recursor => true,
        backend_install => true,
    } ->
    powerdns::config { 'recursor-allow-from':
        type => 'recursor',
        setting => 'allow-from',
        value => $dns_listen_range,
    } ->
    powerdns::config { 'recursor-forward-zones':
        type => 'recursor',
        setting => 'forward-zones',
        value => "sonyc=$openvpn_dns_list",
    } ->
     powerdns::config { 'recursor-forward-zones-recurse':
        type => 'recursor',
        setting => 'forward-zones-recurse',
        value => ".=$dns_ip_addrs",
    } ->     
    powerdns::config { 'recursor-local-address':
        type => 'recursor',
        setting => 'local-address',
        value => $dns_listen_local,
    } -> File['resolv.conf'] 
```

Some changes to the SSH configuration was needed for the setup. SSH is normally used to connect to servers with static IPs. As such, by default, OpenSSH is configured to warn the user if the IP address of the remote computer changes. Since the OpenVPN IP of the nodes is expected to dynamically change, this warning is unneeded and can lead to insensitivity to future warnings. As such, we disable the warning. 

In its place, we enable the visual display of the host keys for the remote nodes. These are small ASCI art diagrams representing the remote cryptographic key. In theory, an administrator connecting to a spoofed node could realize something is wrong if the art changes. At the very least, it is harmless.  

We have also started to configure [host-based authentication] for allowing the control server to authenticate itself to the clients. Ideally, it would be possible to disable password-based authentication on the PI, making unauthorized access over the network a lot more difficult. Additionally, it would make the experience of accessing the nodes from the ingestion server a lot more covenant. So far, we have enabled the setting to allow host-based authentication on the control server. However, we still need to create a keypair, install it on the control server, and put the public key on the sensor nodes. This would require some thought as to ensuring the security and the back up of the key to make sure it does not fall into the wrong hands. 

The puppet code for the SSH changes is as folows:
```ruby
    #Since client ip addrs can change, we need to disable the check.
    ssh_config { "CheckHostIP":
      ensure => present,
      value  => "no",
    }
    ssh_config { "VisualHostKey":
      ensure => present,
      value  => "yes",
    }
    ssh_config { "HostbasedAuthentication":
      ensure => present,
      value  => "yes",
    }    
```

We run an [ElasticSearch] instance on the control server. Its purpose is two-fold. First, the instance acts as a tiebreaker when there is an even number of ingestion servers, preventing a split-brain situation. Second, the instance on the control server acts as a load balancer for the ElasticSearch cluster.

Currently, an emergency hot patch has been applied to the control server to disable its ability to be a master node. We have not yet propagated this change to the Puppet environment. We have found the ElasticSearch environment is unstable when the control server is elected master. The Puppet environment should be updated ASAP. 

The Puppet code for the control server is almost identical to the code for the ingestion server. The only difference is that the ```master_only``` pram is set to true. Note that when the above fix is applied, the name will be misleading as the node will be unable to be a master. 

[Nginx] is used to allow some clients to connect to the ElasticSearch cluster through the control server using a password instead of the ElasticSearch API certificate. For security, only GET requests are allowed through Nginx. See the section on Nginx below

Here is the code that instantiates the ElasticSearch class. See the ingestion server section or [elasticsearch.pp] for the details of the class. 
```
    class{'sonyc::elasticsearch' :
        local_elasticsearch_host => $local_elasticsearch_host,
        elasticsearch_hosts => $elasticsearch_hosts,
        master_only => true
    }
``` 

Historically, the control server was the host for the instrumentation's teams dashboards.  There has been a move away from hosting these servers on the control server due to limited resources, issues with access from outside NYU's campus, and security concerns. However, legacy, albert still useful, dashboards still reside on the control server. 

The original instrumentation dashboard was created to provide a demonstration of how the new backend could provide useful information at a glance. It is based on Drupal, with a custom module that connects to the backend ElasticSearch database. Unfornatuantly, the code is no longer maintained and is inherently insecure. To prevent the security issues from being exploited, and HTTP password is needed before accessing the Drupal site. 

The Drupal dashboard runs on top of PHP, with site-specific data stored in a [MySQL]/[MariaDB] database.  There are two custom Drupal modules and one custom theme that is stored as zip files in the GIT repository. The [SONYC data module] is a Drupal module that enables access to the data stored in the ElasticSearch database. The [Drupal visualization module] is a fork of the Drupal Visualization API which allows for the display of graphs. We have created some custom modifications to better suit our use case. The [Drupal SONYC Theme] is a custom theme designed to be similar to the SONYC website at the time of its creation.

Drupal runs on top of Apache on port 8081 in /var/www/sonyc_cp. It is proxied via Nginx (see below).  

The puppet code defining both the Drupal site and the [MySQL]/[MariaDB] database is below. Note that some information is redacted. 

```ruby
 #These are used for the drupal site template
    $drupal_database = 'drupaldb'
    $drupal_database_username = 'drupal'
    $drupal_database_password = '<redacted>'
    $drupal_database_host = 'localhost'
    
    class { '::mysql::server':
      root_password    => 'babcc216842e3',
      override_options => { 
            'mysqld' => { 
                'max_connections' => '1024',
                'innodb_large_prefix'  => 'true',
                'innodb_file_format'   => 'barracuda',
                'innodb_file_per_table'=> 'true',
            } 
      },
      databases => {
        "${drupal_database}" => {
           ensure  => 'present',
           charset => 'utf8',
        },
        "${grafana_database}" => {
           ensure  => 'present',
           charset => 'utf8',
        },       
      },
      users => {
          "${drupal_database_username}@localhost" => {
            ensure                   => 'present',
            password_hash            =>  mysql_password($drupal_database_password),
          },
          "${grafana_database_username}@localhost" => {
            ensure                   => 'present',
            password_hash            =>  mysql_password($grafana_database_password),
          }
      },
      grants => {
          "${drupal_database_username}@localhost/${drupal_database}.*" => {
            ensure     => 'present',
            options    => ['GRANT'],
            privileges => ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'INDEX', 'ALTER', 'CREATE TEMPORARY TABLES'],
            table      => "${drupal_database}.*",
            user       => "${$drupal_database_username}@localhost",
          },
          "${grafana_database_username}@localhost/${grafana_database}.*" => {
            ensure     => 'present',
            options    => ['GRANT'],
            privileges => ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'INDEX', 'ALTER', 'CREATE TEMPORARY TABLES'],
            table      => "${grafana_database}.*",
            user       => "${$grafana_database_username}@localhost",
          },         
      }
    }

 class { '::php':
        extensions => {
            'pdo' => {},
            'pdo_mysql' => {
                provider => 'none'
            },
        }
    } ->
    class{'mysql::bindings':
        php_enable => true
    } 
    php::extension{ 'gd':
    }->
    package { 'php5-gd':
    }
    
    php::extension{'curl':
    }->
    package{'php5-curl':
    }
    php::extension{'mbstring':
    }
    
    class { 'apache':
        default_vhost => false,
        mpm_module => 'prefork',
    } 
    
    include apache::mod::php
    include apache::mod::rewrite
    class{ 'drupal':
        drush_path => "/usr/bin/env php5 /usr/local/bin/drush"
        
    }
    file {'/tmp/drupal_sonyc_data.zip':
        source => 'puppet:///modules/sonyc/drupal_sonyc_data.zip'
    }
    
    file {'/tmp/drupal_sonyc_theme.zip':
        source => 'puppet:///modules/sonyc/drupal_sonyc_theme.zip'
    }
    
    file {'/tmp/drupal_visualization.zip':
        source => 'puppet:///modules/sonyc/drupal_visualization.zip'
    }
    
    package {'unzip': }
    
    drupal::site { 'sonyc_cp':
        core_version => '8.2.5',
        settings_content => template('sonyc/drupal-settings-8.php.erb'),
        require => [
            CLASS['php'],
            Package['httpd'],
            CLASS['apache'],
            CLASS['::mysql::server'],
            CLASS['mysql::bindings'],
            FILE['/tmp/drupal_sonyc_data.zip'],
            FILE['/tmp/drupal_sonyc_theme.zip'],
            FILE['/tmp/drupal_visualization.zip'],
            PACKAGE['unzip']
        ],
        modules => {
            'devel' => '1.0-beta1',   
            'leaflet' => '1.0-beta1',
            'ctools'  => '3.0-alpha27',
            'entity' => '1.0-alpha4',
            'geofield' => '1.0-alpha2',          
            'geocoder' => '2.0-alpha5',
            'geophp' => '1.0-beta1',
            'field_validation' => '1.0-alpha5',
            'bootstrap_layouts' => '4.1',   
            'layout_plugin' => '1.0-alpha23',         
            'ds' => '2.6',
            'libraries' => '3.x-dev',
            'advagg' => '2.0',
            'diff' => '1.0-rc1',
            'css_editor' => '1.0',
            'sonyc_data' => {
              'download'  => {
                'type' => 'file',
                'url'  => 'file:///tmp/drupal_sonyc_data.zip',
               },
            },
            'visualization' => {
              'download'  => {
                'type' => 'file',
                'url'  => 'file:///tmp/drupal_visualization.zip',
               },
            },
        },
        themes  => {
            'bootstrap' => '3.1',
            'sonyc_theme' => {
             'download' => {
                'type' => 'file',
                'url'  => 'file:///tmp/drupal_sonyc_theme.zip',
              },
            },
         },
         libraries => {
            'leaflet' => {
              'download'       => {
                'type' => 'file',
                'url'  => 'http://cdn.leafletjs.com/leaflet/v1.0.2/leaflet.zip',
                'sha256'  => '365ba270463d05bd164cb9f793ab3c89751633757402e1fbd6646b2fcdf4d767',
              },
              'destination'    => 'sites/all/libraries',
              'directory_name' => 'leaflet',
            },
        },
    }->
    exec{"/bin/bash -c 'cd /var/www/sonyc_cp && sudo composer config repositories.drupal composer https://packages.drupal.org/8 && sudo composer require phayes/geophp && sudo composer update && sudo composer install'":
        cwd => '/var/www/sonyc_cp',
        returns => [0,1]
    }

    apache::vhost { 'vhost':
        ip      => '127.0.0.1',
        port    => '8081',
        manage_docroot => false,
        docroot => '/var/www/',
        rewrites => [],
        override => 'ALL'
    }

```

[Kibana] is a data visualization platform for exploring data within [ElasticSearch]. Kibana provides a convent tool to explore and visualize the status updates as well as server metrics. Kibana runs on port 5601 and is proxied by Nginx (See below). Here is the defining Puppet code.  

```ruby
    CLASS['sonyc::elasticsearch'] ->
    class { 'kibana4':
      package_repo_version => '5.x',
      version => '5.0.2',
      manage_repo => false,
      package_url => 'https://artifacts.elastic.co/downloads/kibana/kibana-5.0.2-amd64.deb',
      config => {
        'server.port'                  => 5601,
        'server.host'                  => '127.0.0.1',
        'elasticsearch.url'            => "https://$local_elasticsearch_host:9200/",
        'elasticsearch.preserveHost'   => true,
        'elasticsearch.ssl.cert'       => "/etc/ssl/elasticsearch_api/elasticsearch_api.pem",
        'elasticsearch.ssl.key'        => "/etc/ssl/elasticsearch_api/elasticsearch_api_key.pem",
        'elasticsearch.ssl.ca'         => "[/etc/ssl/elasticsearch_api/CA.pem]",
        'elasticsearch.ssl.verify'     => true,
        'kibana.index'                 => '.kibana',
        'kibana.defaultAppId'          => 'discover',
        'server.basePath' 		 	   => '/kibana',
        #'server.ssl.key'               => '/path/to/your/ssl/key',
        #'server.ssl.cert'              => '/path/to/your/ssl/cert',
        'logging.dest'                 => '/var/log/kibana/kibana.log',
        'logging.verbose'              => true,
        'tilemap.url'                  => 'http://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        'tilemap.options.maxZoom'      => 18,
        'tilemap.options.minZoom'      => 10,
        'tilemap.options.attribution'  => 'Map data ©OpenStreetMap contributors',
        'tilemap.options.subdomains'   => ['a','b','c']
      },
      subscribe => [ SONYC::SSL_REQUEST['elasticsearch_api'] ]
    }
```

[Nginx] is utilized as a proxy to connect the various web consoles and services to the network. Nginx also performs HTTP authentication. Nginx looks at ```/etc/nginx/.htpasswd```. This is a [standard htpasswd file] that can be edited in the usual way. On the Vagrant test environment, a user "vagrant" with password "vagrant" and a user "elasticsearch" with password "elasticsearch" is automatically created. In the actual environment, the users and passwords need to be managed manually. 

Care is taken with the ElasticSearch virtual host to prevent users from being able to modify or delete data in the cluster. First, an "elasticsearch-api-block-sp" is used to block access to the "_cluster", "_nodes", or "_shutdown" URLs. Second, the proxy will any request other than HTTP "GET" requests. 

In the test environment, there is a GIT server to allow the ingestion server and virtual clients to request the SONYC python code. It servers repositories from /var/repos which are cloned from the submodules of the [SONYC Test Automation GIT].

There is a special "web_services" certificate used in the control server. Unlike the other certificates, this one signed by a public certificate authority. In the production environment, it is used for the web services to ensure users that they are connected to the actual control server and not spoof or man in the middle attack. On the Vagrant test environment, this certificate is self-signed leading web browsers to display the appropriate error. 

There is also the beginning of the infrastructure for storing [certificate revocation lists] (CRLs) on the controls server. These should be stored in /usr/share/nginx/html/crl/. However, we have not yet fully implemented checking for the CRLS. 

The following table shows the different virtual hosts running on Nginx, the authentication needed, as well the backend service it connects to, and the URL to access it.

|    Virtual Host   |                        Backend Service             |       URL      |
|-------------------|----------------------------------------------------|----------------|
|root               |files from /usr/share/nginx/html/                   |default locaiton|
|sonyc-kibana       |http://<span></span>127.0.0.1:5601/                 |/kibana/        |
|sonyc-drupal       |http://<span></span>127.0.0.1:8081/sonyc_cp/        |/sonyc_cp/      |
|elasticsearch-api  |https://<span></span>$local_elasticsearch_host:9200/|/elasticsearch/ |
|git (Vagrant only) |git repos from /var/repos                           |/git/           |

Here is the puppet configuration for Nginx:

```ruby
    package { 'git':
        ensure => 'installed'
    } -> VCSREPO<| |>
    
    package { 'git-core':
        ensure => 'installed'
    } -> VCSREPO<| |>
    
    #Clone the current git
    file { '/var/repos':
        ensure => 'directory',
    } 
    if $sonyc_node_repo
    {
        FILE['/var/repos'] -> 
        vcsrepo { '/var/repos/sonycnode':
            ensure   => latest,
            provider => git,
            source   => $sonyc_node_repo, 
            revision => 'master'
        }
    }
    
    if $sonyc_server_repo
    {
        FILE['/var/repos'] -> 
        vcsrepo { '/var/repos/server':
            ensure   => latest,
            provider => git,
            source   => $sonyc_server_repo, 
            revision => 'master'
        }
    }
    sonyc::ssl_request { 'web_service':
        sign_cert_extra_terms => 'signing_server'
    } 
    class { 'nginx::config': } 
    
    package { 'fcgiwrap':
        ensure => 'installed'
    } ->Class['::nginx::service']
    
    class { 'nginx': 
        #package_name => 'nginx-extras'
    } 
    
    #Overide fastcgi_params
    CLASS['nginx::package'] -> 
    file { "${::nginx::config::conf_dir}/fastcgi_params":
      ensure  => present,
      mode    => '0770',
      content => template('sonyc/fastcgi_params.erb'),
    } ->
    NGINX::RESOURCE::LOCATION<| |>
    
    CLASS['nginx::package'] -> 
    file {"${::nginx::config::conf_dir}/.htpasswd":
        owner => 'www-data',
        group => 'www-data',
        mode => '400'
    }
    
    CLASS['nginx::package'] -> 
    file {"${::nginx::config::conf_dir}/elasticsearch.htpasswd":
        owner => 'www-data',
        group => 'www-data',
        mode => '400'
    }  
    if $::is_vagrant {
        $password_for_web = 'vagrant'; #fqdn_rand_string(8,'','password')
        notice("Password for user vagrant will be:  $password_for_web  ")
        $cryptpasswd_for_web = ht_md5($password_for_web,fqdn_rand_string(8,'','password'))
        CLASS['nginx::package'] -> 
        htpasswd { 'vagrant':
            cryptpasswd => $cryptpasswd_for_web,  # encrypted password
            target      => "${::nginx::config::conf_dir}/.htpasswd",
        } ->
        File["${::nginx::config::conf_dir}/.htpasswd"] ->
        NGINX::RESOURCE::LOCATION<| |>
        
        $password_for_es = 'elasticsearch'; #fqdn_rand_string(8,'','password')
        notice("Password for user elasticsearch for the elasticsearch proxy will be:  $password_for_es  ")
        $cryptpasswd_for_es = ht_md5($password_for_es,fqdn_rand_string(8,'','password2'))
        CLASS['nginx::package'] -> 
        htpasswd { 'elasticsearch':
            cryptpasswd => $cryptpasswd_for_es,  # encrypted password
            target      => "${::nginx::config::conf_dir}/elasticsearch.htpasswd",
        } ->
        File["${::nginx::config::conf_dir}/elasticsearch.htpasswd"] ->
        NGINX::RESOURCE::LOCATION<| |>    
        
    }
    
    CLASS['nginx::package'] -> 
    nginx::resource::upstream { 'kibana4':
      members => [
        '127.0.0.1:5601',
      ],
    } 
    
    CLASS['nginx::package'] -> 
    nginx::resource::upstream { 'apache':
      members => [
        '127.0.0.1:8081',
      ],
    } 
    
    #CLASS['nginx::package'] -> 
    #nginx::resource::upstream { 'grafana_server':
    #  members => [
    #    '127.0.0.1:8134',
    #  ],
    #} 
    
    CLASS['nginx::package'] -> 
    nginx::resource::upstream { 'elasticsearchapi':
      members => [
        "$local_elasticsearch_host:9200",
      ],
      subscribe => [ SONYC::SSL_REQUEST['elasticsearch_api'] ]
    } 
    
    
    CLASS['nginx::package'] -> 
    nginx::resource::vhost { 'http':
        use_default_location => false, 
        ssl => false,
        access_log => '/var/log/nginx/http.access_log',
        error_log => '/var/log/nginx/http.error_log'
    } 
    nginx::resource::location { 'http-root':
        vhost => 'http',
        location  => '~ /',
        www_root => '/usr/share/nginx/html/',
        priority => 409,
        #rewrite_rules => ['/kibana/(.*) /$1']
    }
    
    
    CLASS['nginx::package'] -> 
    nginx::resource::vhost { 'sonyc':
        use_default_location => false, 
        ssl => true,
        listen_port => 443,
        ssl_cert  => '/etc/ssl/web_service/web_service.pem',
        ssl_key   => '/etc/ssl/web_service/web_service_key.pem',
        ssl_protocols => 'TLSv1 TLSv1.1 TLSv1.2',
        ssl_ciphers => $sonyc::ngix_ciphers,
        ssl_session_timeout => '1d',
        ssl_session_tickets => 'off',
        access_log => '/var/log/nginx/sonyc.access_log',
        error_log => '/var/log/nginx/sonyc.error_log'
    } 
    CLASS['nginx::package'] -> NGINX::RESOURCE::LOCATION<| |>
    
    
    nginx::resource::location { 'sonyc-root':
        vhost => 'sonyc',
        ssl_only => true,
        location  => '/',
        www_root => '/usr/share/nginx/html/',
        auth_basic => "Admins Only!",
        auth_basic_user_file => "${::nginx::config::conf_dir}/.htpasswd",
        priority => 499,
        #rewrite_rules => ['/kibana/(.*) /$1']
    } -> 
    nginx::resource::location { 'sonyc-kibana':
        vhost => 'sonyc',
        ssl_only => true,
        location  => '~ /kibana/(?<kibana_url>.*)',
        #www_root => '/home/sonyc/production_server',
        proxy_pass_header => ['Server'],
        proxy_set_header => [
            'Host $http_host',
            'X-Real-IP $remote_addr',
            'X-Scheme $scheme',
            ],
        auth_basic => "Admins Only!",
        auth_basic_user_file => "${::nginx::config::conf_dir}/.htpasswd",
        proxy => 'http://kibana4/$kibana_url',
        priority => 404,
        #rewrite_rules => ['/kibana/(.*) /$1']
    } -> 
    nginx::resource::location { 'sonyc-drupal':
        vhost => 'sonyc',
        ssl_only => true,
        location  => '~ /sonyc_cp/(?<drupal_url>.*)',
        #www_root => '/home/sonyc/production_server',
        proxy_pass_header => ['Server'],
        #http://drupal.stackexchange.com/questions/102091/drupal-behind-a-ssl-offloading-reverse-proxy-is-this-config-correct
        proxy_set_header => [
            'Host $host',
            'X-Forwarded-For $proxy_add_x_forwarded_for',
            'X-FORWARDED-PROTO $scheme',
            'X-Real-IP $remote_addr',
            'X-CLUSTER-CLIENT-IP $remote_addr',
            'X-FORWARDED-PORT 443',
            ],
        auth_basic => "Admins Only!",
        auth_basic_user_file => "${::nginx::config::conf_dir}/.htpasswd",
        proxy => 'http://apache/sonyc_cp/$drupal_url$is_args$query_string',
        priority => 405,
    }->
    nginx::resource::location { 'elasticsearch-api-block-sp':
        #https://stackoverflow.com/questions/28388861/use-nginx-as-proxy-to-prevent-create-update-delete-operations-on-elasticsearch-v
        vhost => 'sonyc',
        ssl_only => true,
        location  => '~* ^/elasticsearch/(_cluster|_nodes|_shutdown)',
        auth_basic => "Admins Only!",
        auth_basic_user_file => "${::nginx::config::conf_dir}/.htpasswd",
        location_deny  =>  ["all"],
        priority => 406,
    }->
    nginx::resource::location { 'elasticsearch-api':
        vhost => 'sonyc',
        ssl_only => true,
        location  => '/elasticsearch/',
        proxy_pass_header => ['Server'],
        #http://drupal.stackexchange.com/questions/102091/drupal-behind-a-ssl-offloading-reverse-proxy-is-this-config-correct
        proxy_set_header => [
            'Host $host',
            'X-Forwarded-For $proxy_add_x_forwarded_for',
            'X-FORWARDED-PROTO $scheme',
            'X-Real-IP $remote_addr',
            'X-CLUSTER-CLIENT-IP $remote_addr',
            ],
        auth_basic => "Admins Only!",
        auth_basic_user_file => "${::nginx::config::conf_dir}/elasticsearch.htpasswd",
        proxy => 'https://elasticsearchapi/',
        location_cfg_append => {
            'proxy_ssl_certificate' => "/etc/ssl/elasticsearch_api/elasticsearch_api.pem",
            'proxy_ssl_certificate_key' => "/etc/ssl/elasticsearch_api/elasticsearch_api_key.pem",  
            'proxy_ssl_trusted_certificate' =>     "/etc/ssl/elasticsearch_api/CA.pem"
        },
        raw_append => [
        "limit_except GET {
            deny all;
        }
        " ],
        priority => 407,
    }
   if $::is_vagrant {
        nginx::resource::location { '/git/.*/git-receive-pack$':
            vhost => 'http',
            location  => '~ /git/.*/git-receive-pack$',
            location_deny => ['all'],
            priority => 408,
        } 
    
        #https://www.toofishes.net/blog/git-smart-http-transport-nginx/
        nginx::resource::location { '/git/*':
            vhost => 'http',
            www_root => "/usr/lib/git-core/",
            location  => '~ /git(/.*)',
            fastcgi => 'unix:/var/run/fcgiwrap.socket',
            fastcgi_param => {
                'SCRIPT_FILENAME' => '/usr/lib/git-core/git-http-backend',
                'SCRIPT_NAME' => '/usr/lib/git-core/git-http-backend',
                'GIT_HTTP_EXPORT_ALL' => '""',
                'GIT_PROJECT_ROOT' => '/var/repos',
                'PATH_INFO' => '$1'
            },
            priority => 409,
        }
    }
    
    CLASS['nginx::package'] -> 
    file{ '/etc/nginx/conf.d/default.conf' : 
        ensure => absent,
        notify => Class['::nginx::service']
    } 
    CLASS['nginx::package'] -> 
    file{ '/etc/nginx/conf.d/default' : 
        ensure => absent,
        notify => Class['::nginx::service']
    }
    CLASS['nginx::package'] -> 
    file{ '/etc/nginx/sites-enabled/default.conf' : 
        ensure => absent,
        notify => Class['::nginx::service']
    } 
    CLASS['nginx::package'] -> 
    file{ '/etc/nginx/sites-enabled/default' : 
        ensure => absent,
        notify => Class['::nginx::service']
    }
    #http://serverfault.com/questions/416254/adding-an-existing-user-to-a-group-with-puppet
    CLASS['nginx::package'] -> 
    exec {"www-data shadow membership":
        unless => "/usr/bin/getent group shadow | /usr/bin/cut -d: -f4| /bin/grep -q www-data",
        command => "/usr/sbin/usermod -a -G shadow www-data",
    }
    pam { "allow normal login for nginx":
      ensure    => present,
      service   => 'nginx',
      type      => 'auth',
      control   => '[success=ok new_authtok_reqd=ok ignore=ignore user_unknown=bad default=die]',
      module    => 'pam_securetty.so',
      position  => 'before module pam_deny.so',
    }
    
       
    #create a storage for crl
    CLASS['nginx::package'] -> 
    file { '/usr/share/nginx/html/crl/':
        ensure => 'directory',
    }
```

We have created a tool that allows the instrumentation team to see the status of the nodes. All the user needs to do is run the command "[node_last_update]". (For convenience, It is also available on the ingestion server.)

It is configured by the puppet statement below. 

```ruby
file { "/usr/bin/node_last_update":
      ensure  => present,
      mode    => '0755',
      content => template('sonyc/node_last_update.erb'),
    }
```


There are a number of open ports on the control server that are needed to function. These are defined using iptables, in addition to the rules listed above to allow OpenVPN to function. The following table summarises all the iptables rules (all ports are TCP unless otherwise noted): 

|    port   |          rule name        |            usage            |                                 notes                            |
|-----------|---------------------------|-----------------------------|------------------------------------------------------------------|
|All        |000 Let vagrant connect    |vagrant ssh or other access  |only on test environment and only for eth0 (connection to host)   |
|icmp       |007 accept all icmp        |allow icmp packets           |Allow ping and other icmp packets                                 |
|22         |020 allow ssl access       |Allow SSH access to server   |                                                                  |
|9200 & 9300|022 Allow Elasticsearch    |Elasticsearch cluster and api|                                                                  |
|80         |521 Allow http             |HTTP requests                |                                                                  |
|443        |522 Allow https from client|REST API                     |Open to outside of NYU network (configured via NYU firewall by IT)|
|53 (tcp)   |601 Allow DNS: tcp         |DNS name resolution          |Only on Vagrant test environment.                                 |
|53 (udp)   |602 Allow DNS: udp         |DNS name resolution          |Only on Vagrant test environment.                                 |
  
For reference, here is the full iptable configuration for the control server:

```ruby
  
    #Firewall
    sysctl{ 'net.ipv4.ip_forward': value => '1' }
    sysctl{ 'net.ipv6.conf.all.disable_ipv6': value => '1' }
    sysctl{ 'net.ipv6.conf.default.disable_ipv6': value => '1' }
    
    resources{ 'firewall':
      purge => true,
    }

        
    class ingestion_server_fw_pre {
        Firewall {
            require => undef,
        }
        #If we are running from vagrant, make sure we don't lock ourselvs out
        if $is_vagrant {
          firewall { '000 Let vagrant connect':
            chain     => "INPUT",
            iniface => 'eth0',
            proto  => 'all',
            action => 'accept',
            before => [],
          }    
   
        }
          firewall { '001 accept established connections':
            chain     => "INPUT",
            proto  => 'all',
            state  => ['RELATED', 'ESTABLISHED'],
            action => 'accept',
            before => [],
          }     
          
          firewall { '002 accept established connections':
            chain     => "OUTPUT",
            proto  => 'all',
            state  => ['RELATED', 'ESTABLISHED'],
            action => 'accept',
            before => [],
          }  

         firewall { '002 accept loopback':
            chain     => "INPUT",
            proto  => 'all',
            iniface => 'lo',
            action => 'accept',
            before => [],
         }           
         
         firewall { '003 accept loopback':
            chain     => "OUTPUT",
            proto  => 'all',
            outiface => 'lo',
            action => 'accept',
            before => [],
         }

        #Block vpn tunnal trafic from the wrong device
        firewall { '005 reject spoofed tun0 trafic':
            chain     => "INPUT",
            proto  => 'all',
            iniface => '! tun0',
            action => 'reject',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            before => [],
         }

         firewall { '006 reject spoofed tun1 trafic':
            chain     => "INPUT",
            proto  => 'all',
            iniface => '! tun1',
            action => 'reject',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            before => [],
         }        
         
         #Allow ICPM
         firewall { '007 accept all icmp':
            proto  => 'icmp',
            action => 'accept',
         }   
         
         
        #Connect the two tunnels (if it is from the correct device) 
        firewall { '011 reject spoofed tun0 trafic':
            chain     => "FORWARD",
            proto  => 'all',
            iniface => '! tun0',
            action => 'reject',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            before => [],
         }

         firewall { '012 reject spoofed tun1 trafic':
            chain     => "FORWARD",
            proto  => 'all',
            iniface => '! tun1',
            action => 'reject',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            before => [],
         }   
         
        #http://serverfault.com/questions/431593/iptables-forwarding-between-two-interface
        firewall { '013 fowared tun1 to tun0':
            chain     => "FORWARD",
            physdev_in => 'tun1',
            iniface => 'tun1',
            outiface => 'tun0',            
            proto  => 'all',
            action => 'accept',
            src_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
            dst_range => "10.$openvpn_server_index.128.0-10.$openvpn_server_index.255.255",
        }
        
        firewall { '014 fowared tun0 to tun1':
            chain     => "FORWARD",
            physdev_in => 'tun0',
            iniface => 'tun0',
            outiface => 'tun1',            
            proto  => 'all',
            action => 'accept',
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
            dst_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.127.255",
        }      

        firewall { '015 nat tun0':
           table    => 'nat',
           chain    => 'POSTROUTING',
           jump     => 'MASQUERADE',
           proto 	=> 'all',
           physdev_out => 'tun0',
        }


        firewall { '016 nat tun1':
           table    => 'nat',
           chain    => 'POSTROUTING',
           jump     => 'MASQUERADE',
           proto 	=> 'all',
           physdev_out => 'tun1',
        }
        
        #nat 10.254.254.254 to the current server
        firewall { '017 tun0 nat 10.254.254.254':
           table    => 'nat',
           chain    => 'PREROUTING',
           jump     => 'DNAT',
           iniface => 'tun0',
           proto 	=> 'all',
           destination => '10.254.254.254',
           todest => "10.$openvpn_server_index.0.1" 
        }

        #allow incoming ssh and openvpn connections, regardless of where they are from
        firewall { '020 allow ssl access':
            chain     => "INPUT",
            dport   => [22],
            proto  => tcp,
            action => accept,
        }
        
         firewall { '021 allow OpenVPN access':
            chain     => "INPUT",
            dport   => [1194, 1195],
            proto  => udp,
            action => accept,
        }       
        

        firewall { '022 Allow Elasticsearch':
            chain     => "INPUT",
            dport   => [9200,9300],
            proto  => tcp,
            action => accept,
        }
        #Allow DNS over the tunnals
        firewall { '023 Allow DNS: tcp':
            chain     => "INPUT",
            dport   => [53],
            proto  => 'tcp',
            action => accept,
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.255.255",
        }

        firewall { '023 Allow DNS: udp':
            chain     => "INPUT",
            dport   => [53],
            proto  => 'udp',
            action => accept,
            src_range => "10.$openvpn_server_index.0.0-10.$openvpn_server_index.255.255",
        }
        
         firewall { '522 Allow https from client':
            chain     => "INPUT",
            dport   => [443],
            proto  => tcp,
            action => accept,
        }       
        
    }

    class ingestion_server_fw_post {
        firewallchain { 'INPUT:filter:IPv4':
          policy => 'drop',
          before => [],
        }  ->
        firewallchain { 'INPUT:filter:IPv6':
          policy => 'drop',
          before => [],
        } ->
        firewallchain { 'OUTPUT:filter:IPv6':
          policy => 'drop',
          before => [],
        }  
    } 
    
    Firewall {
      require => Class['sonyc::ingestion_server::ingestion_server_fw_pre'],
      before  => Class['sonyc::ingestion_server::ingestion_server_fw_post'],
    }

    class{ ['sonyc::ingestion_server::ingestion_server_fw_pre', 'sonyc::ingestion_server::ingestion_server_fw_post']: }

    
    class { 'firewall': }
```

### Data Access
The data access server is also accessible by SSH from anywhere on the NYU network. It uses the VIDA domain accounts for logging in and user management.  Tandon IT needs to add additional users. Each user has access to their VIDA home directory and project directories, which they can use to transfer files. 

The data access server does not have an equivalent in the test environment, nor does it have a puppet script to configure it. Instead, it is fully configured by Tandon IT. Its main purpose is to grant users access to '/mount/vida-sonyc/' without needed them to give them access to the ingestion servers. To simplify the process of pulling the data, a number of scripts are available in the [sonycanalysis repository]. 

### Data Decryption
The data decryption server can be SSHed into from CUSP's development network. It has both an encryption key and a password that are both stored on physical paper. The encryption key is needed to boot the server, while the password is required for SSH access. 

The heart of the data decryption service is the python based [data decryption server]. The sensor nodes use a public encryption key to encrypt the random AES key used to encrypt each audio recording.  The service accepts these encrypted AES keys returns the decrypted AES keys. In the future, it could also log the requests to help detect unauthorized access. 

Like the ingestion servers, the decryption server runs a number of instances of the python service; particularly ports 8000-8004. The python services are managed by [supervisord]. It is run out of '/home/sonyc/data_decryption', which, on the production environment, must be cloned from the  [data decryption server] repository. The server accepts settings from '[/etc/data_decryption_settings.cnf]' and obtains its private keys from '/home/sonyc/decryption_keys'. 

The python service is configured by the following code:
```ruby
    package{ 'python-tornado':
        ensure => 'installed'
    }
    package{ 'git':
        ensure => 'installed'
    } -> VCSREPO<| |>
    
    user{ 'sonyc': 
        managehome => true,
        home => '/home/sonyc',
    }

    if $data_decryption_repo {
        USER['sonyc'] -> 
        vcsrepo { '/home/sonyc/data_decryption':
            ensure   => latest,
            provider => git,
            source   => $data_decryption_repo, 
            revision => 'master'
        } ~> SUPERVISORD::PROGRAM <| |>
    }
    

    package{ 'libffi-dev':
        ensure => 'installed'
    }  
    
    package{ 'libssl-dev':
        ensure => 'installed'
    }
    
    package{ 'python-crypto':
        ensure => 'installed'
    } ~> CLASS['supervisord']
    
    python::pip{ 'python-cryptography':
        pkgname => 'cryptography',
        
        require =>[ PACKAGE['libffi-dev'],
                    PACKAGE['libssl-dev'],
                  ]
    }
    
    #SONYC Server
    EXEC['install pip'] -> CLASS['supervisord']
    CLASS['python'] ->
    class{ 'supervisord':
      install_pip => false, #pip should already be installed
    } 
    #The server config file 
    $data_decryption_port = 443
    $data_decryption_key_dir = '/home/sonyc/decryption_keys'
    
    
    file{ "$data_decryption_key_dir":
        ensure  => directory,
    } -> 
    file{ '/etc/data_decryption_settings.cnf':
        ensure  => file,
        content => template('sonyc/data_decryption_settings.cnf.erb'),
    }
    $sonyc_ports = [8000,8001,8002,8003,8004]
    
    $sonyc_ports.each |$sonyc_port| {
    File['/etc/data_decryption_settings.cnf']~>
        supervisord::program{ "data_decryption_$sonyc_port":
          command             => "python /home/sonyc/data_decryption/data_decryption_server.py --port=$sonyc_port",
          priority            => '100',
          program_environment => {
            'PYTHONPATH'   => '/home/sonyc/server'
          },
          require =>[ 
                      USER['sonyc']
                    ]
        } 
    }
    
    supervisord::rpcinterface{ 'rpcinterface':
      rpcinterface_factory => 'supervisor.rpcinterface:make_main_rpcinterface'
    }

```

Users of the service can specify which private key to use to decrypt the AES key. If no name is provided, "default_key.pem" is used. In the production environment, this key must be manually added by the administrator. In the vagrant test environment, this key is added automatically by puppet:

```ruby
    if $::is_vagrant {
        FILE[ "$data_decryption_key_dir" ] ->
        file { "$data_decryption_key_dir/default_key.pem":
              source => '/vagrant/var/audio_enc.pem'
              #subscribe =>[ 
              #            EXEC[ 'make_private_key']
              #          ]
        } ~> SUPERVISORD::PROGRAM <| |>
    }
```

An [Nginx] proxy is used to link the python services to the outside world. This proxy is responsible for ensuring that clients have a valid 'file_access' client certificate.  It checks these certificates based on a local [CRL] stored at '/etc/ssl/file_access/file_access.crl'. It is imperative that this file is updated whenever a 'file_access' certificate is revoked. The Nginx is fully configured by:

```ruby
    #ngix
    class{ 'nginx::config': } 
    class{ 'nginx': } 


    CLASS['nginx::package'] -> 
    nginx::resource::upstream { 'backends':
      members => $sonyc_ports.map |$sonyc_port| {"127.0.0.1:$sonyc_port"}
    } 
    
    
    CLASS['nginx::package'] -> 
    nginx::resource::vhost { 'sonyc-localhost':
        ssl => true,
        listen_port => 443,
        ssl_cert  => '/etc/ssl/file_access/file_access.pem',
        ssl_key   => '/etc/ssl/file_access/file_access_key.pem',
        ssl_client_cert => '/etc/ssl/file_access/CA.pem',
        ssl_crl => '/etc/ssl/file_access/file_access.crl',
        ssl_protocols => 'TLSv1 TLSv1.1 TLSv1.2',
        ssl_ciphers => $sonyc::ngix_ciphers,
        ssl_session_timeout => '1d',
        ssl_session_tickets => 'off',

        
        use_default_location => false, 
        access_log => '/var/log/nginx/sonyc.access_log',
        error_log => '/var/log/nginx/sonyc.error_log',
        

        
        subscribe => [ SONYC::SSL_REQUEST['file_access'] ]
    } 
    CLASS['nginx::package'] -> 
    nginx::resource::location{ 'sonyc-localhost-root':
        vhost => 'sonyc-localhost',
        ssl_only => true,
        location  => '/',
        #www_root => '/home/sonyc/production_server',
        proxy_pass_header => ['Server'],
        proxy_set_header => [
            'Host $http_host',
            'X-Real-IP $remote_addr',
            'X-Scheme $scheme',
            'X-Client-Cert $ssl_client_cert',
            'X-Client-SDN $ssl_client_s_dn'
            ],
        proxy => 'http://backends',
    }

    CLASS['nginx::package'] -> 
    file{ '/etc/nginx/conf.d/default.conf' : 
        ensure => absent,
        notify => Class['::nginx::service']
    }
```
In the production environment, the only ports open are 22 for SSH and 443 for HTTPS. Note that, in the production environment,  port 22 is further restricted to CUSP's development network by an NYU firewall.  In the test environment, additional ports are open to allow Vagrant to communicate with the VM. This is summarised by the following table: 

|    port   |          rule name        |            usage            |                                 notes                            |
|-----------|---------------------------|-----------------------------|------------------------------------------------------------------|
|All        |000 Let vagrant connect    |vagrant ssh or other access  |only on test environment and only for eth0 (connection to host)   |
|22         |020 allow ssl access       |Allow SSH access to server   |in preduction, restricted to CUSP's development network by an NYU |
|443        |522 Allow https from client|REST API                     |Open to outside of NYU network (configured via NYU firewall by IT)|
  
For convenience, here is the full iptable configuration: 

```ruby
    #Firewall
    sysctl{ 'net.ipv4.ip_forward': value => '1' }
    sysctl{ 'net.ipv6.conf.all.disable_ipv6': value => '1' }
    sysctl{ 'net.ipv6.conf.default.disable_ipv6': value => '1' }
    
    resources{ 'firewall':
      purge => true,
    }

        
    class data_decryption_fw_pre {
        Firewall {
            require => undef,
        }
        #If we are running from vagrant, make sure we don't lock ourselvs out
        if $is_vagrant {
          firewall { '000 Let vagrant connect':
            chain     => "INPUT",
            iniface => 'eth0',
            proto  => 'all',
            action => 'accept',
            before => [],
          }    
   
        }
          firewall { '001 accept established connections':
            chain     => "INPUT",
            proto  => 'all',
            state  => ['RELATED', 'ESTABLISHED'],
            action => 'accept',
            before => [],
          }     
          
          firewall { '002 accept established connections':
            chain     => "OUTPUT",
            proto  => 'all',
            state  => ['RELATED', 'ESTABLISHED'],
            action => 'accept',
            before => [],
          }  

         firewall { '002 accept loopback':
            chain     => "INPUT",
            proto  => 'all',
            iniface => 'lo',
            action => 'accept',
            before => [],
         }           
         
         firewall { '003 accept loopback':
            chain     => "OUTPUT",
            proto  => 'all',
            outiface => 'lo',
            action => 'accept',
            before => [],
         }

    

        #allow incoming ssh and openvpn connections, regardless of where they are from
        firewall { '020 allow ssh access':
            chain     => "INPUT",
            dport   => [22],
            proto  => tcp,
            action => accept,
        }
        
         firewall { '522 Allow https from client':
            chain     => "INPUT",
            dport   => [443],
            proto  => tcp,
            action => accept,
        }       
        
    }

    class data_decryption_fw_post {
        firewallchain { 'INPUT:filter:IPv4':
          policy => 'drop',
          before => [],
        }  ->
        firewallchain { 'INPUT:filter:IPv6':
          policy => 'drop',
          before => [],
        } ->
        firewallchain { 'OUTPUT:filter:IPv6':
          policy => 'drop',
          before => [],
        }  
    } 
    
    Firewall {
      require => Class['sonyc::data_decryption_server::data_decryption_fw_pre'],
      before  => Class['sonyc::data_decryption_server::data_decryption_fw_post'],
    }

    class{ ['sonyc::data_decryption_server::data_decryption_fw_pre', 'sonyc::data_decryption_server::data_decryption_fw_post']: }

    
    class { 'firewall': }
```

### Certificate Authority 
The CA server is air gaped, it is only accessible physically. An encryption key is needed to boot it. This key is stored both on a physical paper as well as on a flash drive that can be inserted to boot it. Once booted, it requires an account to access the stored scripts. 




[Puppet]: https://puppet.com/docs/puppet/4.10/index.html
[the language documentation]: https://puppet.com/docs/puppet/4.10/lang_summary.html


[SONYC environment directory]: [https://github.com/sonyc-project/SONYC_Test_Automation/tree/master/src/puppet_environments/sonyc]

[SONYC Test Automation GIT]: https://github.com/sonyc-project/SONYC_Test_Automation
["manifest" subdirectory]: https://github.com/sonyc-project/SONYC_Test_Automation/tree/master/src/puppet_environments/sonyc/manifests
["modules/sonyc/" subdirectory]: https://github.com/sonyc-project/SONYC_Test_Automation/tree/master/src/puppet_environments/sonyc/modules/sonyc
["modules" subdirectory]: https://github.com/sonyc-project/SONYC_Test_Automation/tree/master/src/puppet_environments/sonyc/modules

[Vagrent]: https://www.vagrantup.com/
[Brooklyn Research Cluster]: https://brooklyn.hpc.nyu.edu

[sonycserver git]: https://github.com/sonyc-project/sonycserver/tree/d09d21490c70944824f6e888277c7df7087e74b4
[supervisord]: http://supervisord.org/
[Nginx]: https://www.nginx.com/
[move_finished_files.sh]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/files/move_finished_files.sh
[archive_files.sh]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/files/archive_files.sh
[archive_one_folder.sh]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/files/archive_one_folder.sh
[default.pp]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/manifests/default.pp
[actual.pp]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/manifests/actual.pp
[ingestion_server.pp]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/manifests/ingestion_server.pp
[learn-address.sh]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/templates/learn-address.sh.erb
[ElasticSearch]: https://www.elastic.co/
[Search Guard]: https://github.com/floragunncom/search-guard
[elasticsearch.pp]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/manifests/elasticsearch.pp
[init_elasticsearch.sh]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/templates/init_elasticsearch.sh.erb
[fluentd]: https://www.fluentd.org/
[dstat]: https://www.fluentd.org/datasources/dstat

[control_server.pp]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/manifests/control_server.pp
[PowerDNS Recursor]: https://www.powerdns.com/recursor.html
[host-based authentication]: https://en.wikibooks.org/wiki/OpenSSH/Cookbook/Host-based_Authentication
[SONYC data module]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/files/drupal_sonyc_data.zip
[Drupal visualization module]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/files/drupal_visualization.zip
[Drupal SONYC Theme]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/files/drupal_sonyc_theme.zip
[MySQL]: https://www.mysql.com/
[MariaDB]: https://mariadb.org/
[Kibana]: https://www.elastic.co/products/kibana
[standard htpasswd file]: https://httpd.apache.org/docs/2.4/programs/htpasswd.html
[certificate revocation lists]: https://en.wikipedia.org/wiki/Certificate_revocation_list
[node_last_update]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/templates/node_last_update.erb

[sonycanalysis repository]: https://github.com/sonyc-project/sonycanalysis
[data decryption server]: https://github.com/sonyc-project/data_decryption

[/etc/data_decryption_settings.cnf]: https://github.com/sonyc-project/SONYC_Test_Automation/blob/master/src/puppet_environments/sonyc/modules/sonyc/templates/data_decryption_settings.cnf.erb
[CRL]: https://en.wikipedia.org/wiki/Certificate_revocation_list
