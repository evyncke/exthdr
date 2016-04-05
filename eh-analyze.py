#!/usr/bin/python


# To be run after eh-scan.py
# this script compares the traceroutes w/ and w/o extension headers and fills exthdr_summary
# from exthdr1M or bgp_exthdr

import mysql.connector
import GeoIP
import re
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
source = config.scan['source']

dbConnection = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database=db_db, port=db_port)
dbCursor = dbConnection.cursor(buffered=True)
dbCursor.raise_on_warnings = True

gi = GeoIP.open("/usr/share/GeoIP/GeoIPASNumv6.dat", GeoIP.GEOIP_STANDARD)

if source == "alexa":
    dbInsert = ("REPLACE INTO exthdr_summary VALUES(%s, %s, %s, %s, %s, %s, %s, %s)")
    dbClean = ("DELETE FROM exthdr_summary")
    select_table = "exthdr"
elif source == "bgp":
    dbInsert = ("REPLACE INTO bgp_exthdr_summary VALUES(%s, %s, %s, %s, %s, %s, %s, %s)")
    dbClean = ("DELETE FROM bgp_exthdr_summary")
    select_table = "bgp_exthdr"


def addr2Name(addr):
    if (addr == ''):
        return addr
    try:
        hostname, aliaslist, ipaddrlist = socket.gethostbyaddr(addr)
        return hostname
    except:
        return addr

# Return the ASN name based on a AS number
def asn2name(asn):
    # Should we get the name?
    # $ dig +short AS23028.asn.cymru.com TXT
    # "23028 | US | arin | 2002-01-04 | TEAMCYMRU - SAUNET"

	return ''

# Return the ASN name based on a router address
# TODO: missing Toronto, torix.ca
# https://en.wikipedia.org/wiki/List_of_Internet_exchange_points_by_size
def addr2Asn(addr):
    global gi, dbConnection

    # AMS-IX addresses are like 2001:7f8:1::/64 embedding the ASN in decimal
    # 2001:7f8:30::A506:4523:1/64 => 16-bit ASN of 64523
    # 2001:7f8:30::A500:19:5000:1/64 => 32-bit ASN of 195000
    if re.match('^2001:7f8:1:', addr):
        try:
            chunks = addr.split(':')
            chunksCount = len(chunks)
            lowChunk = int(chunks[chunksCount - 2], 10)
            if chunks[chunksCount - 4] == 'a500':
                highChunk = int(chunks[chunksCount - 3], 10)
            else:
                highChunk = int(chunks[chunksCount - 3][3], 10)
            asn = 10000 * highChunk + lowChunk
            print "This is a AMS-IX address: ", addr, " ===> AS", str(asn)
#            return "AS" + str(asn) + ' ' + asn2Name(asn)
            return "AS" + str(asn)
        except:
            pass

    # V-IX addresses are like 2001:7f8:30::/64 embedding the ASN in decimal
    # 2001:7f8:1::0001:zzzz:zzzz/64 => 16-bit ASN of 64523
    # 2001:7f8:1::10zz:zzzz:zzzz/64 => 32-bit ASN of 195000
    # See https://www.vix.at/vix_ipv6.html?L=1
    if re.match('^2001:7f8:30:', addr):
        try:
            chunks = addr.split(':')
            chunksCount = len(chunks)
            lowChunk = int(chunks[chunksCount - 1], 10)
            if int(chunks[chunksCount - 3], 10) >= 1000: # 32-bit ASN
                highChunk = int(chunks[chunksCount - 2], 10)
            else:
                highChunk = int(chunks[chunksCount - 2], 10) + 1000 * int(chunks[chunksCount - 3][2:3], 10)
            asn = 10000 * highChunk + lowChunk
            print "This is a V-IX address: ", addr, " ===> AS", str(asn)
#            return "AS" + str(asn) + ' ' + asn2Name(asn)
            return "AS" + str(asn)
        except:
            pass

    # LINX addresses are like 2001:7f8:4:*::61e5:* where 61e5 is the ASN in hexadecimal
    # or 2001:7f8:4:*::3:1232:* where 3 1232 is the 32-bit ASN in hexadecimal
    if re.match('^2001:7f8:4:', addr):
        try:
            chunks = addr.split(':')
            chunksCount = len(chunks)
            lowChunk = int(chunks[chunksCount - 2], 16)
            highChunk = int(chunks[chunksCount - 3], 16) if chunks[chunksCount - 3] != '' else 0
            asn = 65536 * highChunk + lowChunk
            print "This is a LINX address: ", addr, " ===> AS", str(asn)
#            return "AS" + str(asn) + ' ' + asn2Name(asn)
            return "AS" + str(asn)
        except:
            pass

    # 2001:7f8:14:: are AS6881 NIX.CZ, z.s.p.o.
    # 2001:7f8:54:: are AS57734 FranceIX
    # no real logic so let's use a database :-(
    if re.match('^2001:7f8:14:', addr) or re.match('^2001:7f8:54:', addr):
        try:
            dbCursor = dbConnection.cursor(buffered=True)
            dbCursor.execute("select asn, as_name from ixp where address = %s", (addr, ))
            row = dbCursor.fetchone()
            if row != None:
                (asn, as_name) = row
                return "AS" + str(asn) + ' ' + as_name
        except:
            pass


            # Else, return the MAXMIND free geolite information as "AS12956 Telefonica Backbone Autonomous System"
    return gi.name_by_addr_v6(addr)

# Should be more tricky as some organization (Yahoo & Google) have multiple
# AS26101 Yahoo! AS36647 Yahoo  AS26085 Yahoo! AS36646 Yahoo AS36129 Yahoo AS26316 AltaVista Company
# AS38689 Yahoo! Korea, Corp. AS55517 YAHOO! HKA  AS23926 Yahoo Search Marketing Japan
# are all AS10310 Yahoo!  
# Google is also: AS24424 Beijing Gu Xiang Information Technology Co.,Ltd. => AS15169 Google
# Saudi Telecom: AS39891 Saudi Telecom Company JSC AS25019 SaudiNet, Saudi Telecom Company 
# AS7843 Time Warner Cable Internet LLC: AS20001 Time Warner Cable Internet LLC AS11426 Time Warner Cable Internet LLC AS11427 
# AS1299 TeliaSonera International Carrier: AS3301 TeliaSonera AB 
# AS7473 Singapore Telecommunications Ltd: AS132804 Singapore Telecommunications Limited
# AS2914 NTT America, Inc. AS4713 NTT Communications Corporation AS38639 NTT Communications Corporation 
# AS6453 Tata Communications AS4755 TATA Communications formerly VSNL is Leading ISP
def canonicalAsn(asn):
	if asn == 'AS23926' or asn == 'AS26101' or asn == 'AS26085' or asn == 'AS26316' or asn == 'AS36129' or asn == 'AS36646' or asn == 'AS36647' or asn == 'AS38689' or asn == 'AS55517':
		return 'AS10310'
	if asn == 'AS24424':
		return 'AS15169'
	if asn == 'AS39891':
		return 'AS25019'
	if asn == 'AS20001' or asn == 'AS11426' or asn == 'AS11427':
		return 'AS7843'
	if asn == 'AS3301':
		return 'AS1299'
	if asn == 'AS132804':
		return 'AS7473'
	if asn == 'AS4713' or asn == 'AS38639':
		return 'AS2914'
	if asn == 'AS4755':
		return 'AS6453'

	return asn


def eqAsn(asn1, asn2):
    if asn1 == None:
        return False
    if asn2 == None:
        return False
    if asn1 == asn2:
        return True
    chunks1 = asn1.split(' ')
    chunks2 = asn2.split(' ')
    return canonicalAsn(chunks1[0]) == canonicalAsn(chunks2[0])


def analyze(test_nb, address, normalRouters, testRouters, normalMessages, testMessages, domain):
    global verbose, dbConnection, dbInsert

    if (verbose):
        print "\n"
        print normalRouters
        print normalMessages
        print testRouters
        print testMessages
    last = len(normalRouters) - 1
    # Need to compute a /48 prefix as well
    network = IPNetwork(address + "/48")
    prefix = str(network.network)
    print "Working on ", address
    asn = addr2Asn(address)
    print "from ", asn
    local_cursor = dbConnection.cursor(buffered=True)
    local_cursor.raise_on_warnings = True
    # First test case: address does not appear as the last normalRouter, i.e., not reached...
    if (source == "alexa" and address != normalRouters[last]) \
            or (source == "bgp" and not eqAsn(asn, addr2Asn(normalRouters[last]))):
        print "\t not reached..."
        local_cursor.execute(dbInsert, (address, domain, prefix, asn, test_nb, 'not reached', None, None))
    else:
        last_common = last
        while last_common >= 0:
            if normalRouters[last_common] != '' and normalRouters[last_common] == testRouters[last_common]:
                break
            last_common -= 1

        if last_common == -1:
            print "\t No router in common ! Packets filtered by your ISP ?"
            local_cursor.execute(dbInsert, (address, domain, prefix, asn, test_nb, 'eh filtered by ISP', None, None))

        elif last_common == last:
            print "\t extension header not dropped"
            local_cursor.execute(dbInsert, (address, domain, prefix, asn, test_nb, 'not dropped', None, None))

        elif last_common == last - 1:
            print "\t extension header dropped at the destination"
            local_cursor.execute(dbInsert, (address, domain, prefix, asn, test_nb, 'destination host drop', address, asn))

        elif normalRouters[last_common + 1] != '' and \
                eqAsn(asn, addr2Asn(normalRouters[last_common + 1])):
            print "\t probably dropped in destination ASN ", asn, "by router ", normalRouters[last_common + 1], \
                addr2Name(normalRouters[last_common + 1])
            local_cursor.execute(dbInsert, (address, domain, prefix, asn, test_nb, 'destination AS drop',
                                            normalRouters[last_common + 1], asn))

        elif eqAsn(asn, addr2Asn(normalRouters[last_common])):
            print "\t probably dropped in destination ASN ", asn
            local_cursor.execute(dbInsert, (address, domain, prefix, asn, test_nb, 'destination AS drop', None, asn))

        elif normalRouters[last_common + 1] != '':
            print "\t probably dropped in transit ASN ", normalRouters[last_common + 1], addr2Name(
                normalRouters[last_common + 1]), addr2Asn(normalRouters[last_common + 1])
            local_cursor.execute(dbInsert, (address, domain, prefix, asn, test_nb, 'transit AS drop',
                                            normalRouters[last_common + 1],  addr2Asn(normalRouters[last_common + 1])))
        else:
            # Catching all other cases...
            print "\t unexpected case"
            local_cursor.execute(dbInsert, (address, domain, prefix, asn, test_nb, 'unknown', None, None))
    dbConnection.commit()
    local_cursor.close()

# Let's remove all previous data
dbCursor.execute(dbClean)

select = "select g.address as address, g.hop as ghop, g.router as grouter, g.message as gmessage, t.hop as thop, " \
         "t.router as trouter, t.message as tmessage, t.domain as tdomain, g.domain as gdomain from " + select_table + " as g join " + select_table + " as t " \
         "on g.address = t.address and g.hop = t.hop and g.test = 0 and t.test = %s order by address, ghop"

for test_nb in range(1, 14):
    print "Running test ", test_nb
    dbCursor.execute(select, (test_nb,))
    currentAddress = ''
    for (address, ghop, grouter, gmessage, thop, trouter, tmessage, tdomain, gdomain) in dbCursor:
        if (currentAddress != address):
            if (currentAddress != ''):  # if not the first line being read
                analyze(test_nb, currentAddress, normalRouters, testRouters, normalMessages, testMessages, tdomain)
            normalRouters = []
            normalMessages = []
            testRouters = []
            testMessages = []
            currentAddress = address
        normalRouters.append(grouter)
        normalMessages.append(gmessage)
        testRouters.append(trouter)
        testMessages.append(tmessage)
    else:
        if (currentAddress != ''):  # if not the first line being read
            analyze(test_nb, currentAddress, normalRouters, testRouters, normalMessages, testMessages, tdomain)

dbConnection.close()
