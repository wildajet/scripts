#!/usr/bin/python
#
# Author:               Jet Wilda <jet.wilda@gmail.com>
# Modifed by:           Jet Wilda <jet.wilda@gmail.com>
# Last Modified:        10/02/2012
#
# Description:
#       Script to parse out and display the descriptions from scripts in /etc/init.d
#

import sys
import os
import string
import re
import os
import sys
import select


def print_description(servicename):
        """Gets the description for the given initscript or xinet.d script"""
#	try:
	if os.path.isfile("/etc/init.d/" + servicename):
		f = open("/etc/init.d/" + servicename)
	elif os.path.isfile("/etc/xinetd.d/" + servicename):
		f = open("/etc/xinetd.d/" + servicename)
	else:
		print "No such daemon(service)"
		return
#	except IOError, msg:
#		print "/etc/init.d/" + servicename , msg

	initscript = []
	line = f.readline()
	while line:
		if re.match('\A\#', line):
			initscript.append(line)
			line = f.readline()
			continue
		if line.strip()=="":
			line = f.readline()
			continue
		f.close()
		break

	formatted_description = ""

	service_script = initscript

        for i in range(0, len(service_script)):
            if (string.find("%s" % service_script[i], "description:") != -1 ):
                service_script[i] = string.replace(service_script[i], "description:" ,"")
                while (string.find("%s" % service_script[i], "\\") != -1) :
                    service_script[i] = string.replace(service_script[i], "#", "\t")
                    service_script[i] = string.replace(service_script[i], "\\", "\n")
                    service_script[i] = string.strip(service_script[i])
                    formatted_description = formatted_description + " " + service_script[i]
                    i = i + 1

                formatted_description = formatted_description + " " + string.strip(string.replace(service_script[i],"#","\t"))
	
	print formatted_description


def main():
    if os.geteuid() == 0:
	if len(sys.argv) < 2:
		print ("you must pass in name of init.d script")
		sys.exit(0)
	else:
		script=sys.argv[1]
		print_description(script)
    else:
        print _("You must run as root.")
        sys.exit(-1)


if __name__ == "__main__":
    main() 
