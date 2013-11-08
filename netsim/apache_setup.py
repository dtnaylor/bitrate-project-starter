import sys
sys.path.append('../common')

import os
import shutil
import logging
from util import check_output, strip_comments

NETSIM_STRING = '# Modified by netsim'

APACHE_UBUNTU = '/etc/init.d/apache2'
APACHE_UBUNTU_PORTS = '/etc/apache2/ports.conf'
APACHE_UBUNTU_PORTS_BAK = '%s.backup' % APACHE_UBUNTU_PORTS
APACHE_UBUNTU_DEFAULT_SITE = '/etc/apache2/sites-available/default'
APACHE_UBUNTU_SITES_AVAILABLE = '/etc/apache2/sites-available'
APACHE_UBUNTU_SITES_ENABLED = '/etc/apache2/sites-enabled'

APACHE_FEDORA = '/usr/local/apache2/bin/httpd'
APACHE_FEDORA_CONF = '/usr/local/apache2/conf/httpd.conf'
APACHE_FEDORA_CONF_BAK = '/usr/local/apache2/conf/httpd.conf.bak'
APACHE_FEDORA_VIRTUAL_HOST_TEMPLATE = '''

Listen %s:8080
<VirtualHost %s:8080>
    ServerAdmin webmaster@localhost

    DocumentRoot /var/www
    <Directory />
        Options FollowSymLinks
        AllowOverride None
    </Directory>
    <Directory /var/www/>
        Options Indexes FollowSymLinks MultiViews
        AllowOverride None
        Order allow,deny
        allow from all
    </Directory>

</VirtualHost>'''

def is_apache_configured_ubuntu():
    found = False
    try:
        with open(APACHE_UBUNTU_PORTS, 'r') as portsf:
            for line in portsf:
                if NETSIM_STRING in line:
                    found = True
                    break
        portsf.closed
    except Exception as e:
        logging.getLogger(__name__).error(e)
    return found

def is_apache_configured_fedora():
    found = False
    try:
        with open(APACHE_FEDORA_CONF, 'r') as conff:
            for line in conff:
                if NETSIM_STRING in line:
                    found = True
                    break
        conff.closed
    except Exception as e:
        logging.getLogger(__name__).error(e)
    return found

def is_apache_configured():
    #return is_apache_configured_ubuntu()
    return is_apache_configured_fedora()


def configure_apache_fedora(ip_list):
    try:
        # back up the existing httpd.conf
        shutil.copyfile(APACHE_FEDORA_CONF, APACHE_FEDORA_CONF_BAK)

        with open(APACHE_FEDORA_CONF, 'a') as conffile:
            conffile.write('%s\n' % NETSIM_STRING)
            for ip in ip_list:
                conffile.write(APACHE_FEDORA_VIRTUAL_HOST_TEMPLATE % (ip, ip))
        conffile.closed
            

    except Exception as e:
        logging.getLogger(__name__).error(e)

def configure_apache_ubuntu(ip_list):
    try:
        # back up the existing ports.conf
        shutil.copyfile(APACHE_UBUNTU_PORTS, APACHE_UBUNTU_PORTS_BAK)
        with open(APACHE_UBUNTU_PORTS, 'a') as portsfile:
            portsfile.write('%s\n' % NETSIM_STRING)
        portsfile.closed
            
        for ip in ip_list:
            # append virtual hosts to ports.conf
            with open(APACHE_UBUNTU_PORTS, 'a') as portsfile:
                    portsfile.write('\n\nNameVirtualHost %s:8080\n' % ip)
                    portsfile.write('Listen %s:8080' % ip)
            portsfile.closed

            # make a conf file for this virtual host
            confpath = os.path.join(APACHE_UBUNTU_SITES_AVAILABLE, ip)
            with open(APACHE_UBUNTU_DEFAULT_SITE, 'r') as defaultfile:
                with open(confpath, 'w') as conffile:
                    for line in defaultfile:
                        if '<VirtualHost' in line:
                            conffile.write('<VirtualHost %s:8080>\n' % ip)
                        else:
                            conffile.write(line)
                conffile.closed
            defaultfile.closed

            # symlink conf file to sites-enabled
            linkpath = os.path.join(APACHE_UBUNTU_SITES_ENABLED, ip)
            if not os.path.islink(linkpath):
                os.symlink(confpath, linkpath)

    except Exception as e:
        logging.getLogger(__name__).error(e)

# Prepare apache VirtualHost for each server ip in ip_list
def configure_apache(ip_list):
    #configure_apache_ubuntu(ip_list)
    configure_apache_fedora(ip_list)


def reset_apache_fedora(ip_list):
    try: 
        # restore ports.conf from backup
        if os.path.isfile(APACHE_FEDORA_CONF_BAK):
            shutil.move(APACHE_FEDORA_CONF_BAK, APACHE_FEDORA_CONF)
        else:
            logging.getLogger(__name__).warning('Could not find %s' % APACHE_FEDORA_CONF_BAK)
    except Exception as e:
        logging.getLogger(__name__).error(e)

def reset_apache_ubuntu(ip_list):
    try:
        # restore ports.conf from backup
        if os.path.isfile(APACHE_UBUNTU_PORTS_BAK):
            shutil.move(APACHE_UBUNTU_PORTS_BAK, APACHE_UBUNTU_PORTS)
        else:
            logging.getLogger(__name__).warning('Could not find %s' % APACHE_UBUNTU_PORTS_BAK)

        # remove conf files
        for ip in ip_list:
            confpath = os.path.join(APACHE_UBUNTU_SITES_AVAILABLE, ip)
            if os.path.isfile(confpath):
                os.remove(confpath)

            linkpath = os.path.join(APACHE_UBUNTU_SITES_ENABLED, ip)
            if os.path.islink(linkpath):
                os.remove(linkpath)

    except Exception as e:
        logging.getLogger(__name__).error(e)


# Put apache back to normal
def reset_apache(ip_list):
    #reset_apache_ubuntu(ip_list)
    reset_apache_fedora(ip_list)


def restart_apache_fedora():
    check_output('%s -k restart' % APACHE_FEDORA, shouldPrint=True)

def restart_apache_ubuntu():
    check_output('%s restart' % APACHE_UBUNTU, shouldPrint=False)

def restart_apache():
    #restart_apache_ubuntu()
    restart_apache_fedora()
