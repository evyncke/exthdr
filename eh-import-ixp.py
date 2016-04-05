#!/usr/bin/python
import mysql.connector
import re
import urllib2
import csv
import json
from netaddr import *

from config import Config

config = Config()
# MySQL database configuration
db_user = config.db['db_user']
db_password = config.db['db_password']
db_db = config.db['db_db']
db_port = config.db['db_port']
db_host = config.db['db_host']

# Some globals configuration variables
verbose = config.scan['verbose']

dbConnection = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database=db_db, port=db_port)
dbCursor = dbConnection.cursor(buffered=True)
dbCursor.raise_on_warnings = True

# Parse http://www.nix.cz/networks.csv with lines as:
# "Company Name";"www";"ASN";"Peering policy";"Route server";"FENIX";"NOC Contact";"IPv4";"IPv6"
# "ACTIVE 24, s.r.o.";"http://www.active24.cz/";"25234";"Open";"1";"1";"noc@active24.cz";"91.210.16.235,91.210.16.236";"2001:7f8:14::1c:1,2001:7f8:14::1c:2"

def processCZ():
    global dbCursor, dbConnection

    print "Processing NIX.CZ database..."
    response = urllib2.urlopen('http://www.nix.cz/networks.csv')
    for line in csv.reader(response, delimiter=';'):
        (name, www, asn, policy, server, fenix, noc, ipv4, ipv6) = line;
        if re.match('.*:.*', ipv6):
            addresses = ipv6.split(',')
            for address in ipv6.split(','):
                print "Adding: " + address + " as member of AS" + asn + " (" + name + ")"
                dbCursor.execute("insert ignore into ixp (address, asn, as_name) values(%s, %s, %s)",
                                 (address, int(asn), name))
    dbConnection.commit()


# Parse https://www.franceix.net/en/members-resellers/members/
# where there is a javascript variable 'aaData': [{"website": "http://www.1and1.fr/", "capacity": 10, "ipv4s": ["37.49.236.42"], "name": "1&1", "ipv6s": ["2001:7f8:54::42"], "pops": ["TCC"], "asnumber": 8560, "contact": "peering at oneandone.net", "users": true, "favicon": "http://www.1and1.fr/favicon.ico", "gixes": ["FranceIX - Paris"]}, .... repeated

def processFranceIX():
    global dbCursor, dbConnection

    print "Processing FranceIX database..."
    response = urllib2.urlopen('https://www.franceix.net/en/members-resellers/members/')
    for line in response:
        match = re.match(r'.*\'aaData\': \[(.*)\].*', line)
        if match:
            print "Found THE line => "
            jsonData = json.loads('[' + match.group(1) + ']')
            for item in jsonData:
                for address in item['ipv6s']:
                    print "Adding: " + address + " as member of AS" + str(item['asnumber']) + " (" + item['name'] + ")"
                    dbCursor.execute("insert ignore into ixp (address, asn, as_name) values(%s, %s, %s)",
                                     (address, item['asnumber'], item['name']))
            break
    dbConnection.commit()


processCZ()
processFranceIX()

dbConnection.close()
