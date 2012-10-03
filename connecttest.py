#!/usr/bin/python
#
# Author:		this code was found at http://www.unix.com/solaris/38577-how-monitor-ports.html
# Modifed by:           Jet Wilda <jet.wilda@gmail.com>
# Last Modified:        10/02/2012
#
# Description:
#       Script to make a socket connections
#

import socket
import sys

if ( len(sys.argv) != 3 ):
    print "Usage: " + sys.argv[0] + " you must enter IP or FQDN and port"
    sys.exit(1)

remote_host = sys.argv[1]
#print "remote_host is ,%s," % remote_host
remote_port = int(sys.argv[2])
#print "remote_port is ,%s," % remote_port

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.settimeout(60)
try:
        sock.connect((remote_host, remote_port))
except Exception,e:
        pass
        #print "%d closed " % remote_port
else:
        pass
        #print "%d open" % remote_port
sock.close()

#for remote_port in port:
#        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        sock.settimeout(60)
#        try:
#                sock.connect((remote_host, remote_port))
#        except Exception,e:
#                print "%d closed " % remote_port
#        else:
#                print "%d open" % remote_port
#        sock.close()
