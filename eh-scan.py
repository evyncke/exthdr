#!/usr/bin/python

# This script build exthdr based on ALexa top-1M (file downloaded) or from BGP routing table via routeviews.org

from exceptions import OSError
from scapy.all import *
import mysql.connector
import threading
import Queue
import time
import socket
import csv
import os
import datetime
from zipfile import *

import wget
from config import Config

t = time.time()
config = Config()
# MySQL database configuration
db_user = config.db['db_user']
db_password = config.db['db_password']
db_db = config.db['db_db']
db_port = config.db['db_port']
db_host = config.db['db_host']

db_connection = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database=db_db, port=db_port)
db_cursor = db_connection.cursor()
db_cursor.raise_on_warnings = True

# Some globals configuration variables
verbose = config.scan['verbose']
start_hop_limit = config.scan['start_hop_limit']
stop_hop_limit = config.scan['stop_hop_limit']
icmp_data = config.scan['icmp_data']
thread_count = config.scan['thread_count']
addr_parallel = config.scan['addr_parallel']
limit_select = config.scan['limit_select']
timeout = config.scan['timeout']
source = config.scan['source']


l4DH = IPv6ExtHdrDestOpt(options=PadN(optdata='A' * 8)) / TCP(sport=RandShort(), dport=80, flags="S")
l4HbH = IPv6ExtHdrHopByHop(options=PadN(optdata='A' * 8)) / TCP(sport=RandShort(), dport=80, flags="S")
route = ['2001:db8::cafe', '2001:db8::babe'] # Obviously should be better built with first address being scanner node and 2nd address being scanned node
l4RH0 = IPv6ExtHdrRouting(addresses=route, segleft=0, type=0) / TCP(sport=RandShort(), dport=80, flags="S")
l4SRH = IPv6ExtHdrRouting(addresses=route, segleft=0, type=4) / TCP(sport=RandShort(), dport=80, flags="S")
l4AF = IPv6ExtHdrFragment() / TCP(sport=RandShort(), dport=80, flags="S")
l4FH = IPv6ExtHdrFragment(m=1) / TCP(sport=RandShort(), dport=80, flags="S")
l4HbHDH = IPv6ExtHdrHopByHop(options=PadN(optdata='A' * 8)) / IPv6ExtHdrDestOpt(options=PadN(optdata='A' * 8)) /\
          TCP(sport=RandShort(), dport=80, flags="S")
#l4DH128 = IPv6ExtHdrDestOpt(options=PadN(optdata='A' * 120)) / TCP(sport=RandShort(), dport=80, flags="S")     # !!! EVIL ONE
l4DH256 = IPv6ExtHdrDestOpt(options=PadN(optdata='A' * 248)) / TCP(sport=RandShort(), dport=80, flags="S")
l4DH512 = IPv6ExtHdrDestOpt(options=[PadN(optdata='A' * 255), PadN(optdata='A' * 249)]) / TCP(sport=RandShort(), dport=80, flags="S")
#l4HbH128 = IPv6ExtHdrHopByHop(options=PadN(optdata='A' * 120)) / TCP(sport=RandShort(), dport=80, flags="S")	# !!! EVIL ONE
l4HbH256 = IPv6ExtHdrHopByHop(options=PadN(optdata='A' * 248)) / TCP(sport=RandShort(), dport=80, flags="S")
l4HbH512 = IPv6ExtHdrHopByHop(options=[PadN(optdata='A' * 255), PadN(optdata='A' * 249)]) / TCP(sport=RandShort(), dport=80, flags="S")


def cannonize(addr):
#    print "cannonize(" + addr + ")"
    return socket.inet_ntop(socket.AF_INET6, socket.inet_pton(socket.AF_INET6, addr))


def pref(addr):
    #computes /64 prefix of address
    return socket.inet_ntop(socket.AF_INET6, (socket.inet_pton(socket.AF_INET6, addr)[:8] + "\x00" * 8))


def eh_trace(addr, test_name, test_nb, l4, normal_tr, last_hop):
    if verbose:
        print test_name, " TCP traceroute to ", addr
    eh_tr = traceroute6(addr.keys(), l4=l4, minttl=start_hop_limit, maxttl=stop_hop_limit, timeout=timeout,
                        verbose=verbose)[0].get_trace()
    for dest in normal_tr:
        # Iterating over the adresses in normal_tr and not eh_tr is intentionnal. It fixes a bug when an address doesn't
        # return anything in the normal traceroute but does in an eh traceroute, which means we don't know it's last hop
        for hop in range(start_hop_limit, last_hop[dest] + 1):
            d = cannonize(dest)
            try:
                response = eh_tr[dest][hop]
                db_args = (d, addr[d], test_nb, hop, cannonize(response[0]), ('OK' if response[1] else 'TE'))
                results_queue.put(db_args)
            except KeyError:
                db_args = (d, addr[d], test_nb, hop, '', 'TO')
                results_queue.put(db_args)


def get_ip(domain):
    if domain.count("/"):
        domain = domain.split("/")[0]
    try:
        ip = socket.getaddrinfo(domain, None, socket.AF_INET6)[0][4][0]
    except:
        try:
            ip = socket.getaddrinfo("www." + domain, None, socket.AF_INET6)[0][4][0]
        except:
            raise OSError("No AAAA record for this domain")

    return ip


def test_host(addr):
    global verbose, start_hop_limit, stop_hop_limit

    if verbose:
        print "Normal TCP traceroute to ", addr
    normal_tr = traceroute6(addr.keys(), minttl=start_hop_limit, maxttl=stop_hop_limit, timeout=timeout,
                            verbose=verbose)[0].get_trace()
    last_hop = {}
    for dest in normal_tr:
        i = 0

        for hop in normal_tr[dest]:
            if hop > i:
                i = hop

        a = ''
        last_hop[dest] = 0

        for hop in range(start_hop_limit, i + 1):
            try:
                if normal_tr[dest][hop][0] != '' and normal_tr[dest][hop][0] != a:
                    a = normal_tr[dest][hop][0]
                    last_hop[dest] = hop
            except KeyError:
                pass

        for hop in range(start_hop_limit, last_hop[dest] + 1):
            d = cannonize(dest)
            try:
                response = normal_tr[dest][hop]
                db_args = (d, addr[d], 0, hop, cannonize(response[0]), ('OK' if response[1] else 'TE'))
                results_queue.put(db_args)
            except KeyError:
                db_args = (d, addr[d], 0, hop, '', 'TO')
                results_queue.put(db_args)

    eh_trace(addr, "Destination Header 16B", 1, l4DH, normal_tr, last_hop)
    eh_trace(addr, "HbH 16B", 2, l4HbH, normal_tr, last_hop)
    eh_trace(addr, "RH0", 3, l4RH0, normal_tr, last_hop)
    eh_trace(addr, "SRH", 4, l4SRH, normal_tr, last_hop)
    eh_trace(addr, "Atomic Fragment", 5, l4AF, normal_tr, last_hop)
    eh_trace(addr, "Fragment Header", 6, l4FH, normal_tr, last_hop)
    eh_trace(addr, " HbH 16B + Dest Header 16B", 7, l4HbHDH, normal_tr, last_hop)
#    eh_trace(addr, "Destination Header 128B", 8, l4DH128, normal_tr, last_hop)
    eh_trace(addr, "Destination Header 256B", 9, l4DH256, normal_tr, last_hop)
    eh_trace(addr, "Destination Header 512B", 10, l4DH512, normal_tr, last_hop)
#    eh_trace(addr, "HbH 128B", 11, l4HbH128, normal_tr, last_hop)
    eh_trace(addr, "HbH 256B", 12, l4HbH256, normal_tr, last_hop)
    eh_trace(addr, "HbH 512B", 13, l4HbH512, normal_tr, last_hop)


def consumer_thread():
    global work_queue

    print threading.current_thread().name + ": thread starting..."
    myData = threading.local()
    while True:
        if not work_queue.empty():
            try:
                myData.addresses = work_queue.get(block=True, timeout=1)
                if verbose:
                    print threading.current_thread().name + ": queue is not empty processing: ", myData.addresses
                test_host(myData.addresses)
                if verbose:
                    print threading.current_thread().name + ": processing of ", myData.addresses, " is done"
                work_queue.task_done()
            except Queue.Empty:
                if no_more_jobs.is_set():
                    break
        elif no_more_jobs.is_set():
            break

        time.sleep(0.5)

    print threading.current_thread().name + ": thread ending..."


def db_write_thread():
    global results_queue, verbose

    db_connection = mysql.connector.connect(user=db_user, password=db_password, host=db_host, database=db_db,
                                            port=db_port)
    db_cursor = db_connection.cursor()
    writes = 0

    while True:
        if not results_queue.empty():
            try:
                db_args = results_queue.get(block=True, timeout=1)
                db_cursor.execute(db_insertStatement, db_args)
                writes += 1
                if writes > 20:
                    db_connection.commit()
                    writes = 0
                if verbose:
                    print "Writing to DB : ", db_args
            except Queue.Empty:
                if jobs_finished.is_set():
                    break
        elif jobs_finished.is_set():
            break
        else:
            time.sleep(0.5)

    db_cursor.close()
    db_connection.commit()
    db_connection.close()


work_queue = Queue.Queue(thread_count + 2)
results_queue = Queue.Queue()
no_more_jobs = threading.Event()
jobs_finished = threading.Event()


# Create all consumer threads
allThreads = []
for i in range(thread_count):
    thisThread = threading.Thread(name='Tracerouter#' + str(i), target=consumer_thread)
    thisThread.daemon = True
    thisThread.start()
    allThreads.append(thisThread)

db_thread = threading.Thread(name="DB Write Thread", target=db_write_thread)
db_thread.start()

if source == "alexa":
    fn = "top-1m.csv.zip"
    try:
        os.remove(fn)
    except OSError:
        pass
    print "Downloading alexa's Top 1M list"
    wget.download("http://s3.amazonaws.com/alexa-static/top-1m.csv.zip", out=fn)
    print "\nDownload finished ! Loading it..."
    with ZipFile(fn) as zip1M:
        csv1M = zip1M.open("top-1m.csv")
        csv_data = csv.reader(csv1M)
        allRows = list(csv_data)
    print "Top 1M list loaded !"

    db_insertStatement = ("REPLACE INTO exthdr(address, domain, test, hop, router, message) "
                      "values(%s, %s, %s, %s, %s, %s)")
    time.sleep(1)

    if limit_select != 0:
        allRows = allRows[0:limit_select]

    tot = len(allRows)
    addresses_group = {}
    tested_prefixes = []
    n = 0
    i = 0

    for (rank, url) in allRows:
        try:
            i += 1
            wget.callback_progress(i, 1, tot, wget.bar_adaptive)
            address = get_ip(url)
            addressPrefix = pref(address)
            if addressPrefix not in tested_prefixes:
                tested_prefixes.append(addressPrefix)
                if verbose:
                    print url, address, addressPrefix, rank
                    print "Adding work on ", address, ". Number of active threads :", threading.active_count()
                addresses_group[address] = url  # Send this to all consumer threads ;-)
                n += 1
                if n >= addr_parallel:
                    work_queue.put(addresses_group)
                    addresses_group = {}
                    n = 0
        except OSError as e:
            if verbose:
                print "!!!! Error DNS for ", url, e.errno, e.strerror
        except SystemExit:
            sys.exit(0)
        except:
            if verbose:
                print "!!!! Error DNS for ", url, sys.exc_info()[0]
    else:
        if len(addresses_group):
            work_queue.put(addresses_group)

elif source == "bgp":
    fn = "bgp.bz2"
    try:
        os.remove(fn)
    except OSError:
        pass

    today = datetime.date.today()
    url = today.strftime("http://archive.routeviews.org/route-views6/bgpdata/%Y.%m/RIBS/rib.%Y%m%d.0000.bz2")
    print "Downloading BGP dump from ", url
    fn = wget.download(url, out=fn)
    print "\nDownload finished ! Loading the prefixes..."
    cmd = "bzcat " + fn + " | perl zebra-dump-parser.pl"

    d = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    out, err = d.communicate()

    allRows = out.splitlines()

    if limit_select != 0:
        allRows = allRows[0:limit_select]


    db_insertStatement = ("REPLACE INTO bgp_exthdr(address, domain, test, hop, router, message) "
                      "values(%s, %s, %s, %s, %s, %s)")

    tot = len(allRows)
    print "Query returned ", tot, " addresses to try"
    time.sleep(1)

    addresses_group = {}
    tested_prefixes = []
    n = 0
    i = 0
    temp = 0

    for row in allRows:
	prefix_group = row.split(" ")[0]
        (prefix, prefix_length) = prefix_group.split("/")
        i += 1
        wget.callback_progress(i, 1, tot, wget.bar_adaptive)
	if int(prefix_length) > 48:
		if verbose:
			print "Ignoring " + prefix + "/" + str(prefix_length)
		continue
        address = cannonize(prefix + "1")
        addressPrefix = pref(address)
        if addressPrefix not in tested_prefixes:
            tested_prefixes.append(addressPrefix)
            if verbose:
                print "Adding work on ",  address,  "/",  str(prefix_length),  ". Number of active threads: ",  threading.active_count()
            addresses_group[address] = ""  # Send this to all consumer threads ;-)
            n += 1
            if n >= addr_parallel:
                work_queue.put(addresses_group)
                addresses_group = {}
                n = 0
    else:
        if len(addresses_group):
            work_queue.put(addresses_group)

print "All items have been queued, waiting for them to finish processing"
no_more_jobs.set()
work_queue.join()

# Wait until all consumer threads have finished
for thisThread in allThreads:
    thisThread.join()

jobs_finished.set()

db_thread.join()

db_connection.close()

print "Finished in ", time.time() - t, "s for ", len(allRows), " addresses"
