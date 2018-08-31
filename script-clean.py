#!/usr/bin/python

import json
import os
import sys

from ansible.parsing.dataloader import DataLoader
from ansible.vars import VariableManager
from ansible.inventory import Inventory
import jinja2
import yaml


### PLEASE SET ENVIRONMENTVARIABLE "DOCBASE" TO POINT TO THE BASE DIRECTORY WITH CONFIGURATION FILES
FILEBASE      = os.environ.get("DOCBASE", "openstack")

INVENTORYFILE = os.environ.get('INVENTORYFILE', '%s/inventory/hosts' % (FILEBASE))

if not os.path.isfile(INVENTORYFILE):
    print "Cannot find %s, please use environment variable DOCBASE to define the configuration base directory" % (INVENTORYFILE)
    sys.exit(1)

# read configuration for role definition
with open("config/config.json", "r") as read_file:
    data = json.load(read_file)



### helper methods
def load_inventory_from_file(inventoryfile):
    inventory = Inventory(
                             loader           = DataLoader(),
                             variable_manager = VariableManager(),
                             host_list        = inventoryfile
                         )
    return inventory

def load_vars_from_file(varsfile):
    vars = yaml.load(open(varsfile))
    return vars

def get_val_from_file(var,file,isarray=False):
    GLOBALSFILE = os.environ.get('GLOBALSFILE', '%s/%s' % (FILEBASE,file))
    vars        = load_vars_from_file(GLOBALSFILE)
    try:
        return vars[var]
    except:
        if isarray == False:
            return "None"
        else:
            return ["None"]

def get_group_len(group):
    return len(get_hosts_in_group(group))




### methods for gather basic informations

# list hosts in inventory
def list_hosts():
    allhosts = []
    for host in inventory.list_hosts():
        allhosts.append(str(host))
    return allhosts

# list groups in inventory
def list_groups():
    allgroups = []
    for group in inventory.list_groups():
        allgroups.append(str(group))
    return allgroups




### group related methods
def get_hosts_in_group(group):
    hosts = []
    for host in inventory.list_hosts(group):
        hosts.append(str(host))
    return hosts




### host related methods
def hostgroup_vars(host,group):
    allhgv = []
    for hgv in inventory._get_hostgroup_vars(host=host, group=group):
        allhgv.append(hgv)
    return allhgv

def get_inventory_hostname(host):
    return inventory.get_vars(host,True)['inventory_hostname']

def get_inventory_hostname_short(host):
    return inventory.get_vars(host,True)['inventory_hostname_short']

# list groups for host
def host_get_groups(host):
    groups      = host.get_groups()
    host_groups = []
    for group in groups:
        host_groups.append(group)
    return host_groups

def get_ansible_host(host):
    return inventory.get_vars(host,True)['ansible_host']

def get_group_names(host):
    return inventory.get_vars(host,True)['group_names']



# network/ip informations related to hosts
def get_management_address_for_host(host):
    management_intf = get_val_from_file("management_interface","inventory/host_vars/%s.yml" % (host))
    nics            = get_val_from_file("network_interfaces","inventory/host_vars/%s.yml" % (host))
    for nic in nics:
        if nic['device'] == management_intf:
            return nic['address']

def get_network_interfaces_for_host(host):
    nics    = get_val_from_file("network_interfaces","inventory/host_vars/%s.yml" % (host))
    allnics = []
    for nic in nics:
        allnics.append(nic['device'])
    return allnics

def get_network_interface_addresses_for_host(host):
    nics          = get_val_from_file("network_interfaces","inventory/host_vars/%s.yml" % (host))
    allnicaddress = []
    for nic in nics:
        try:
            allnicaddress.append("%s (%s)" % (nic['address'],nic['device']))
        except:
            pass
    return allnicaddress

# host related service informations
def get_role_for_host(host):
    allroles = []
    hgs      = get_group_names(host)
    for d in data['config']:
        rolename = d['rolename']
        memb=d['groupmember']
        for m in memb:
            if m['group'] in hgs:
                allroles.append(rolename)
    allroles = list(set(allroles))
    return allroles

def get_ceph_devices_for_host(host):
    devs    = get_val_from_file("devices","inventory/host_vars/%s.yml" % (host), True)
    alldevs = []
    for dev in devs:
        alldevs.append(dev)
    return alldevs


### Basic Informations (global)
def get_header():
    return FILEBASE

def get_resolvconf_nameserver():
    nameserver = get_val_from_file("resolvconf_nameserver","environments/configuration.yml")
    allns      = []
    try:
        for ns in nameserver:
            allns.append(ns)
        return allns
    except:
        return "None"

def get_resolvconf_search():
    searchdom        = get_val_from_file("resolvconf_search","environments/configuration.yml")
    allsearchdomains = []
    allsearchdomains.append(searchdom)
    return allsearchdomains

def get_security_ntp():
    secntps = get_val_from_file("security_ntp_servers","environments/configuration.yml")
    allntp  = []
    try:
        for ntp in secntps: 
            allntp.append(ntp)
        return allntp
    except:
        return ["None"]


def get_openstack_pools_raw():
    ospools  = get_val_from_file("openstack_pools","environments/ceph/configuration.yml", True)
    allpools = []
    for rawpool in ospools: 
        allpools.append(rawpool)
    return allpools

def get_openstack_pools():
    allpools    = []
    GLOBALSFILE = os.environ.get('GLOBALSFILE', '%s/environments/ceph/configuration.yml' % (FILEBASE))
    vars        = load_vars_from_file(GLOBALSFILE)
    raw_pools   = get_openstack_pools_raw()
    for pool in raw_pools:
        if pool.find('{{') != -1:
            pool_name = pool.lstrip('{{').rstrip('}}').strip()
            allpools.append(vars[pool_name]['name'])
        else:
            allpools.append(pool)
    return allpools




### Service related Informations    
def get_ha_status():
    if len(get_hosts_in_group("controller")) > 1:
        return "yes"
    else:
        return "no"

def get_cockpit_status():
    return get_val_from_file("configure_cockpit","environments/configuration.yml")

def get_cephclient_status():
    return get_val_from_file("configure_cephclient","environments/infrastructure/configuration.yml")

def get_openstackclient_status():
    return get_val_from_file("configure_openstackclient","environments/infrastructure/configuration.yml")

def get_rally_status():
    return get_val_from_file("configure_cephclient","environments/infrastructure/configuration.yml")

def get_phpmyadmin_status():
    return get_val_from_file("configure_phpmyadmin","environments/infrastructure/configuration.yml")

def get_ceph_services():
    allservices = []
    if get_group_len("ceph-mds") > 0: 
        allservices.append("mds")
    if get_group_len("ceph-mon") > 0: 
        allservices.append("mon")
    if get_group_len("ceph-osd") > 0: 
        allservices.append("osd")
    if get_group_len("ceph-msd") > 0: 
        allservices.append("msd")
    if len(allservices) == 0:
        return ["None"]
    else:
        return allservices

def get_openstack_services():
    allservices = []
    if get_group_len("cinder") > 0: 
        allservices.append("Cinder")
    if get_group_len("glance") > 0: 
        allservices.append("Glance")
    if get_group_len("heat") > 0: 
        allservices.append("Heat")
    if get_group_len("horizon") > 0: 
        allservices.append("Horizon")
    if get_group_len("keystone") > 0: 
        allservices.append("Keystone")
    if get_group_len("neutron") > 0: 
        allservices.append("Neutron")
    if get_group_len("nova") > 0: 
        allservices.append("Nova")
    if len(allservices) == 0:
        return ["None"]
    else:
        return allservices

def get_openstack_shared_services():
    allservices = []
    if get_group_len("haproxy") > 0: 
        allservices.append("Haproxy")
    if get_group_len("mariadb") > 0: 
        allservices.append("Mariadb")
    if get_group_len("memcached") > 0: 
        allservices.append("Memcached")
    if get_group_len("rabbitmq") > 0: 
        allservices.append("RabbitMQ")
    if get_group_len("redis") > 0: 
        allservices.append("Redis")
    if len(allservices) == 0:
        return ["None"]
    else:
        return allservices

def get_generic_services():
    allservices = []
    allservices.append("Chrony")
    if get_cockpit_status() == True:
        allservices.append("Cockpit (Client)")
    allservices.append("Cron")
    allservices.append("Docker")
    allservices.append("Fluentd")
    if get_group_len("openvswitch") > 0: 
        allservices.append("Open vSwitch")
    allservices.append("Rsyslog")
    if len(allservices) == 0:
        return ["None"]
    else:
        return allservices

def get_manager_services():
    allservices = []
    allservices.append("Ansible Runtime Analysis")
    allservices.append("Ceph-ansible")
    if get_cephclient_status() == True:
        allservices.append("Cephclient")
    if get_cockpit_status() == True:
        allservices.append("Cockpit (Server)")
    allservices.append("Kolla-ansible")
    allservices.append("OSISM-ansible")
    if get_openstackclient_status() == True:
        allservices.append("OpenStackClient")
    if get_rally_status() == True:
        allservices.append("Rally")
    if get_phpmyadmin_status() == True:
        allservices.append("phpMyAdmin")
    if len(allservices) == 0:
        return ["None"]
    else:
        return allservices

def get_monitoring_services():
    allservices = []
    if get_group_len("grafana") > 0: 
        allservices.append("Grafana")
    if get_group_len("kibana") > 0: 
        allservices.append("Kibana")
    if get_group_len("prometheus") > 0: 
        allservices.append("Prometheus")
    if get_group_len("elasticsearch") > 0: 
        allservices.append("ElasticSearch")
    if len(allservices) == 0:
        return ["None"]
    else:
        return allservices

def get_dashboards():
    activedashboards = []
    for d in data['dashboards']:
        name    = d['name']
        methode = d['methode']
        if methode == "group":
            group = d['group']
            if get_group_len(group) > 0:
                activedashboards.append(name)
        elif methode == "fix":
            activedashboards.append(name)
        elif methode == "var":
            querry = d['querry']
            file   = d['file']
            if get_val_from_file(querry,file) != False:
                activedashboards.append(name)
    return activedashboards

def get_dashboard_inturl(dashname):
    kolla_int_vip = get_val_from_file("kolla_internal_vip_address","environments/configuration.yml")
    kolla_ext_vip = get_val_from_file("kolla_external_vip_address","environments/configuration.yml")
    tls = get_val_from_file("kolla_enable_tls_external","environments/kolla/configuration.yml")
    if tls == "None":
        proto = "http://"
    else:
        proto = "https://"
    for d in data['dashboards']:
        if d['name'] == dashname:
            port_int = d['dashboard']['internal']
            url_int  = "%s%s:%s" % (proto,kolla_int_vip,port_int)
            return url_int

def get_dashboard_exturl(dashname):
    kolla_int_vip = get_val_from_file("kolla_internal_vip_address","environments/configuration.yml")
    kolla_ext_vip = get_val_from_file("kolla_external_vip_address","environments/configuration.yml")
    if len(kolla_ext_vip) < 7:
        kolla_ext_vip = kolla_int_vip
    tls = get_val_from_file("kolla_enable_tls_external","environments/kolla/configuration.yml")
    if tls == "None":
        proto = "http://"
    else:
        proto = "https://"
    for d in data['dashboards']:
        if d['name'] == dashname:
            port_ext = d['dashboard']['external']
            url_ext  = "%s%s:%s" % (proto,kolla_ext_vip,port_ext)
            if port_ext != "n/A":
                url_ext = "%s%s:%s" % (proto,kolla_ext_vip,port_ext)
            else:
                url_ext = "n/A"
            return url_ext

def get_apiendpoints():
    activedpiendpoints = []
    for d in data['api_endpoints']:
        if get_group_len(d["group"]) > 0:
            activedpiendpoints.append(d['name'])
    return activedpiendpoints

def get_apiendpoint_inturl(apiname):
    kolla_int_vip = get_val_from_file("kolla_internal_vip_address","environments/configuration.yml")
    kolla_ext_vip = get_val_from_file("kolla_external_vip_address","environments/configuration.yml")
    tls = get_val_from_file("kolla_enable_tls_external","environments/kolla/configuration.yml")
    if tls == "None":
        proto = "http://"
    else:
        proto = "https://"
    for d in data['api_endpoints']:
        if d['name'] == apiname:
            port_int = d['endpoint']['internal']
            url_int  = "%s%s:%s" % (proto,kolla_int_vip,port_int)
            return url_int

def get_apiendpoint_exturl(apiname):
    kolla_int_vip = get_val_from_file("kolla_internal_vip_address","environments/configuration.yml")
    kolla_ext_vip = get_val_from_file("kolla_external_vip_address","environments/configuration.yml")
    if len(kolla_ext_vip) < 7:
        kolla_ext_vip = kolla_int_vip

    tls = get_val_from_file("kolla_enable_tls_external","environments/kolla/configuration.yml")
    if tls == "None":
        proto = "http://"
    else:
        proto = "https://"
    for d in data['api_endpoints']:
        if d['name'] == apiname:
            port_ext = d['endpoint']['external']
            url_ext  = "%s%s:%s" % (proto,kolla_ext_vip,port_ext)
            if port_ext != "n/A":
                url_ext = "%s%s:%s" % (proto,kolla_ext_vip,port_ext)
            else:
                url_ext = "n/A"
            return url_ext



###################################################################
### M A I N 
###################################################################


inventory   = load_inventory_from_file(INVENTORYFILE)
loader      = jinja2.FileSystemLoader(searchpath="templates/")
environment = jinja2.Environment(loader=loader)



# headline 
TEMPLATEFILE                = 'header.j2'
template                    = environment.get_template(TEMPLATEFILE)
result_header               = template.render(get_header=get_header)


# chapter 1.
TEMPLATEFILE                = 'generic.j2'
template                    = environment.get_template(TEMPLATEFILE)
result_generic              = template.render(get_val_from_file=get_val_from_file,
                                              get_resolvconf_search=get_resolvconf_search,
                                              get_resolvconf_nameserver=get_resolvconf_nameserver,
                                              get_security_ntp=get_security_ntp,
                                              get_ha_status=get_ha_status
                                             )


# chapter 2. / 2.1 
TEMPLATEFILE                = 'services_main.j2'
template                    = environment.get_template(TEMPLATEFILE)
result_services_main        = template.render(get_val_from_file=get_val_from_file,
                                              get_generic_services=get_generic_services,
                                              get_openstack_shared_services=get_openstack_shared_services
                                             )


# chapter 2.2
TEMPLATEFILE                = 'services_manager.j2'
template                    = environment.get_template(TEMPLATEFILE)
result_services_manager     = template.render(get_val_from_file=get_val_from_file,
                                              get_manager_services=get_manager_services
                                             )

# chapter 2.3
TEMPLATEFILE                = 'services_openstack.j2'
template                    = environment.get_template(TEMPLATEFILE)
result_services_openstack   = template.render(get_val_from_file=get_val_from_file,
                                              get_openstack_services=get_openstack_services,
                                              get_openstack_shared_services=get_openstack_shared_services
                                             )

# chapter 2.4
TEMPLATEFILE                = 'services_ceph.j2'
template                    = environment.get_template(TEMPLATEFILE)
result_services_ceph        = template.render(get_val_from_file=get_val_from_file,
                                              get_openstack_pools=get_openstack_pools,
                                              get_ceph_services=get_ceph_services
                                             )

# chapter 2.5
TEMPLATEFILE                = 'services_monitoring.j2'
template                    = environment.get_template(TEMPLATEFILE)
result_services_monitoring  = template.render(get_val_from_file=get_val_from_file,
                                              get_monitoring_services=get_monitoring_services
                                             )

# chapter 3
TEMPLATEFILE                = 'endpoints.j2'
template                    = environment.get_template(TEMPLATEFILE)
result_endpoints            = template.render(get_val_from_file=get_val_from_file,
                                              get_dashboard_exturl=get_dashboard_exturl,
                                              get_dashboard_inturl=get_dashboard_inturl,
                                              get_dashboards=get_dashboards,
                                              get_apiendpoints=get_apiendpoints,
                                              get_apiendpoint_inturl=get_apiendpoint_inturl,
                                              get_apiendpoint_exturl=get_apiendpoint_exturl
                                             )

# chapter 4
TEMPLATEFILE               = 'inventory_main.j2'
template                   = environment.get_template(TEMPLATEFILE)
result_inventory_main      = template.render(get_val_from_file=get_val_from_file,
                                             list_hosts=list_hosts,
                                             get_inventory_hostname=get_inventory_hostname,
                                             get_management_address_for_host=get_management_address_for_host
                                            )

# chapter 4.1
TEMPLATEFILE               = 'inventory.j2'
template                   = environment.get_template(TEMPLATEFILE)
result_inventory           = template.render(get_val_from_file=get_val_from_file,
                                             list_hosts=list_hosts,
                                             get_inventory_hostname=get_inventory_hostname,
                                             get_inventory_hostname_short=get_inventory_hostname_short,
                                             get_ansible_host=get_ansible_host,
                                             get_group_names=get_group_names,
                                             get_management_address_for_host=get_management_address_for_host,
                                             get_network_interfaces_for_host=get_network_interfaces_for_host,
                                             get_network_interface_addresses_for_host=get_network_interface_addresses_for_host,
                                             get_role_for_host=get_role_for_host,
                                             get_ceph_devices_for_host=get_ceph_devices_for_host
                                            )
                



#### Output the document as .rst

print result_header
print result_generic
print result_services_main
print result_services_manager
print result_services_openstack
print result_services_ceph
print result_services_monitoring
print result_endpoints
print result_inventory_main
print result_inventory
