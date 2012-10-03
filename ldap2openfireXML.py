#!/usr/bin/env python
# encoding: utf-8
#
# Author:               Jet Wilda <jet.wilda@gmail.com>
# Modifed by:           Jet Wilda <jet.wilda@gmail.com>
# Last Modified:        10/02/2012
#
# Description:
#       Script used to connect to an openLDAP datastore containing XCP jabber users and passwords
#		and then connect to a PostGreSQL database to get the users rosters.  We then create 4 buckets (XML files)
#		of users.
#
"""

Script used to connect to an openLDAP datastore containing XCP jabber users and passwords
and then connect to a PostGreSQL database to get the users rosters.  We then create 4 buckets (XML files)
of users.

Users with no roster
Users with illegal characters in username
All roster items that have illegal characters in the JID along with the user they belong to
All the users with their roster items that can be imported

Some of this code was borrowed from http://returnbooleantrue.blogspot.com/2009/01/converting-ldifldap-data-into-csv-file.html

This code code be a lot cleaner and probably should be split into seperate modules

Created by Jet Wilda on 2010-03-31.

"""

import os
import sys
import getopt
import logging

import ldap
import psycopg2
from copy import deepcopy

# Global Variables
program = None
verbose = False
primaryLogger = None
#Default file names
NOROSTERFILE="usersWithNoRoster.xml"
BADROSTERFILE="usersWithbadRosterItems.xml"
GOODFILE="jibjab2openfireUsers.xml"
BADUSERSFILE="problemUsers.xml"
EXCLUDEFILE="excludedUsers.xml"
LOGFILE="jibjab2openfire.log"

# LDAP Connection information
LDAP_HOST = 'localhost'
LDAP_BASE_DN = 'dc=DOMAIN,dc=tld'
MGR_CRED = 'cn=Manager,dc=DOMAIN,dc=tld'
MGR_PASSWD = 'PASSWORD'
FILTER = ""

#PostGreSQL connection information
PG_HOST="localhost"
PG_DATABASE="xcp"
PG_CRED="USER"
PG_PASSWD="PASSWORD"

EMAIL=False

# usage help message
help_message = '''
This script is used grab information from LDAP and create an openfire XML file
Usage: %s [options]
\t-o GOOD_USERS_XML_FILE       # The XML file that has all the users that should import;
\t                             #  Defaults to jibjab2openfireUsers.xml in the current directory
\t-p PROBLEM_USERS_XML_FILE    # The XML file that contains all the users that won't import
\t                             #  due to haveing invalid characters in their username
\t                             #  Defaults to problemUsers.xml in the current directory
\t-b BAD_ROSTER_ITEMS_XML_FILE # The XML file that has all the bad roster items and the users they go with;
\t                             #  Defaults to usersNbadRosterItems.xml in the current directory
\t-r NO_ROSTER_USERS_XML_FILE  # The XML file that has all the users that don't have any roster items;
\t                             #  Defaults to usersWithNoRoster.xml in the current directory
\t-x EXCLUDE_LIST_TXT_FILE     # A text file with a list of users to exclude, one per line;
\t-f EXCLUDE_LIST_XML_FILE     # The XML file to put the list of excluded users;
\t                             #  Defaults to exludedUsers.xml in the current directory
\t-l LOG_FILE                  # The log file to create defaults to jibjab2openfire.log
\t-m                           # Create the file(s) to email passwords.  Defaults to no|False
\t                             #  if set to True it creates files witht the same name as the XML with a
\t                             #  .email extension
\t-v                           # Verbose output, turns on lots of debug messages to the screen
\t-h                           # print out this help message

i.e. %s 
'''

class Usage(Exception):
    def __init__(self, msg):
        self.msg = msg

#override the print function with debug to be able to turn off and on
def debug (msg):
    """test for verbosity and then print"""
    if verbose:
        print (msg)

# A handler that simply throws away any logging messages sent to it
class NullHandler(logging.Handler):
    def emit(self,record):
        pass

def setupLogging(logfilename=""):
    """ Setup the logger to either log to a file or to a Null handler"""
    global primaryLogger
    primaryLogger = logging.Logger("primaryLogger",logging.DEBUG)

    # Create a handler to print to the log
    if( logfilename != "" ):
        fileHandler = logging.FileHandler(logfilename,"w",encoding=None)
    else:
        fileHandler = NullHandler()

    # Set how the handler will print the pretty log events
    primaryLoggerFormat = logging.Formatter("[%(asctime)s]-[%(lineno)d][%(module)s] - %(message)s",'%m/%d/%y %I:%M%p')
    fileHandler.setFormatter(primaryLoggerFormat)

    # Append handler to the primaryLoggyouer
    primaryLogger.addHandler(fileHandler)

# main class that connects to both LDAP and POSTGRESQL; Also creates the XML files
class XcpUsers:
    """ Class to connect to LDAP and get data"""
    # use the global variables
    global LDAP_HOST
    global LDAP_BASE_DN
    global MGR_CRED
    global MGR_PASSWD
    global PG_HOST
    global PG_DATABASE
    global PG_CRED
    global PG_PASSWD
    global FILTER
    global primaryLogger

    def __init__(self, ldap_host=None, ldap_base_dn=None, mgr_cred=None, mgr_passwd=None, pg_host=None, pg_database=None, pg_cred=None, pg_passwd=None):
        if not ldap_host:
            ldap_host = LDAP_HOST
        if not ldap_base_dn:
            ldap_base_dn = LDAP_BASE_DN
        if not mgr_cred:
            mgr_cred = MGR_CRED
        if not mgr_passwd:
            mgr_passwd = MGR_PASSWD
        if not pg_host:
            pg_host = PG_HOST
        if not pg_database:
            pg_database = PG_DATABASE
        if not pg_cred:
            pg_cred = PG_CRED
        if not pg_passwd:
            pg_passwd = PG_PASSWD
        self.domain = "server.domain.tld"
        self.ldapconn = ldap.open(ldap_host)
        self.ldapconn.simple_bind(mgr_cred, mgr_passwd)
        self.ldap_base_dn = ldap_base_dn
        debug ("connected to the LDAP server %s as %s at base DN %s" %(LDAP_HOST, MGR_CRED,LDAP_BASE_DN))
        primaryLogger.debug ("connected to the LDAP server %s as %s at base DN %s" %(LDAP_HOST, MGR_CRED,LDAP_BASE_DN))
        try:
            self.conn = psycopg2.connect("dbname='%s' user='%s' host='%s' password='%s'" % (pg_database, pg_cred, pg_host, pg_passwd))
            self.cur = self.conn.cursor()
            debug ("connected to the PostGreSQL database %s on server %s as %s " %(pg_database, pg_host,pg_cred))
            primaryLogger.debug ("connected to the PostGreSQL database %s on server %s as %s " %(pg_database, pg_host,pg_cred))
        except:
            # Get the most recent exception
            exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
            # Exit the script and print an error telling what happened.
            sys.exit("Database connection failed!\n ->%s" % (exceptionValue))
        
    def subscriberListGet(self, group):
        """function to return a list subscribers (cn) to a group"""
        # set up the filter on the group name
        gfilter = "(cn=%s)" % group
        # what attribute are we looking for
        key = "jabberCGSubscriber"
        debug ("In function subscriberListGet")
        primaryLogger.debug ("In function subscriberListGet")
        # the results is a list of dictionaries, where the dictionary is a string key and a list of data
        results = self.ldapconn.search_s(self.ldap_base_dn, ldap.SCOPE_SUBTREE, gfilter, [key])
        debug ("Results from the LDAP search are %s" % results)
        # initialize and empty list
        users = []
        for item in results:
            for cn in item[1][key]:
                # split the string into a tuple and then split the string in the second position of that tuple
                users.append(cn.split("=")[1].split(",")[0])
        return users

    def usersInGroupGet(self, group):
        """function to return a list members/users (cn) in the group"""
        # set up the filter on the group name
        gfilter = "(cn=%s)" % group
        # what attribute are we looking for
        key = "member"
        debug ("In function usersInGroupGet")
        primaryLogger.debug ("In function usersInGroupGet")
        # the results is a list of dictionaries, where the dictionary is a string key and a list of data
        results = self.ldapconn.search_s(self.ldap_base_dn, ldap.SCOPE_SUBTREE, gfilter, [key])
        debug ("Results from the LDAP search are %s" % results)
        # initialize and empty list
        users = []
        for item in results:
            for cn in item[1][key]:
                # split the string into a tuple and then split the string in the second position of that tuple
                users.append(cn.split("=")[1].split(",")[0])
        return users

    def groupsGet (self):
        """ function to return a list of all the groups"""
        # what attribute are we looking for
        key = "ou"
        debug ("In function groupsGet")
        primaryLogger.debug ("In function groupsGet")
        # the results is a list of dictionaries, where the dictionary is a string key and a list of data
        results = self.ldapconn.search_s(self.ldap_base_dn, ldap.SCOPE_SUBTREE, '(objectclass=jabbercggroup)', [key])
        debug ("Results from the LDAP search are %s" % results)
        groups = []
        for item in results:
            groups.append(item[1][key][0])
        return groups

    def allUsersGet(self):
        """ function to return a list of dictionaries, where each dictionary is all the information for that user"""
        # all the information attributes we want on this person
        #keys = ['cn','sn','givenName','mail', 'ou', 'uid','userPassword']
        keys = ['cn', 'mail', 'ou', 'uid','userPassword']
        debug ("In function allUsersGet")
        primaryLogger.debug ("In function allUsersGet")
        # the results is a list of dictionaries, where the dictionary is a string key and a list of data
        results = self.ldapconn.search_s(self.ldap_base_dn, ldap.SCOPE_SUBTREE, '(objectclass=person)', keys)
        #debug ("Results from the LDAP search are %s" % results)
        primaryLogger.debug ("Results from the LDAP search are %s" % results)
        users = []
        for item in results:
            userDict = {}
            dict = item[1]
            for key in dict.keys():
                if (key == "uid"):
                    # set the uid
                    userDict[key] = dict[key][0]
                    # get the uid for this username from postgres
                    id = self.idGet(dict[key][0])
                    #debug ("id is %s" % id)
                    # if the user doesn't exist in the database we get back a empty list
                    if ( len(id) <= 0):
                        # since no user then no roster
                        userDict['roster'] = []
                    else:
                        # set the roster to the list of tuples returned
                        userDict['roster'] = self.rosterGet(id[0][0])
                else:
                    userDict[key] = dict[key][0]
            users.append(userDict)
        return users

    def rosterGet(self, userID):
        """return the roster(buddy list i.e. jid, nickname) for the given userID"""
        #query = """SELECT contact_jid, nickname FROM rosters WHERE user_id=%s"""
        #query = """SELECT r.contact_jid, r.nickname, g.group_name FROM rosters r, groups g WHERE r.user_id=%s and r.roster_id = g.roster_id"""
        #query = """SELECT r.contact_jid, r.nickname, g.group_name FROM rosters r, groups g WHERE r.user_id=%s and r.user_id = g.user_id and r.roster_id = g.roster_id"""
        query = """SELECT r.contact_jid, r.nickname, g.group_name FROM rosters r FULL OUTER JOIN groups g ON r.roster_id = g.roster_id WHERE r.user_id=%s"""
        self.cur.execute(query, [userID])
        rows = self.cur.fetchall()
        #debug ("rosterGet results from query [%s] is ,%s," % (query, rows))
        primaryLogger.debug ("rosterGet results from query [%s] is ,%s," % (query, rows))
        return rows

    def idGet(self, username):
        """return the userID for the given username"""
        query = """SELECT user_id FROM users WHERE jid=%s"""
        param = "%s@%s" % (username, self.domain)
        self.cur.execute(query, [param])
        rows = self.cur.fetchall()
        #debug ("idGet results from query [%s] is ,%s," % (query, rows))
        primaryLogger.debug ("idGet results from query [%s] is ,%s," % (query, rows))
        # the rows contains a list of tuples i.e. [(15429,)] or an empty list
        return rows


    def containsAny(self, str, set):
        """ Check to see if there are any characters from set in str. Return true if there are otherwise false"""
        for c in set:
            if c in str: return 1;
        return 0;

    def checkDups(self,seq):
        """Check for any duplicates in the users list, return the duplicates"""
        checked = []
        dups = []
        for e in seq:
            if e not in checked:
                checked.append(e)
            else:
                dups.append(e)
        return dups

    def userNamesGet(self, usersdict):
        """pull out all the usernames and return a list of just the usernames"""
        results = []
        for item in usersdict:
            results.append(item['uid'])
        return results

    def writeXmlHeader(self, output):
        """ Write out the XML header that openfire expects"""
        output.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write("\n")
        output.write("<Openfire>\n")
        
    def writeXmlFooter(self, output):
        """ Write out the XML footer that openfire expects"""
        output.write("</Openfire>\n")
        
    def writeXmlUser(self, output, user, filename):
        """Write out the valuse from the user dictionary into the openfire XML output"""
        output.write("  <User>\n")
        output.write("    <Username>%s</Username>\n" % user['uid'])
        output.write("    <Password>%s</Password>\n" % user['userPassword'] )
        output.write("    <Email>%s</Email>\n" % user['mail'])
        output.write("    <Name>%s</Name>\n" % user['cn'])
        output.write("    <CreationDate>1269250697869</CreationDate>\n")
        output.write("    <ModifiedDate>1269250697869</ModifiedDate>\n")
        if (len(user['roster']) <= 0):
            output.write("    <Roster/>\n")
        else:
            output.write("    <Roster>\n")
            for item in user['roster']:
                # check to make sure the jid has @DOMAIN.TLD in it, otherwise add it.
                if (item[0].find("@") == -1):
                    if (item[1] == ""):
                        output.write('     <Item jid="%s@%s" askstatus="-1" recvstatus="-1" substatus="3">\n' % (item[0], self.domain))
                    else:
                        if ( item[1].find('"') != -1 ):
                            output.write('''     <Item jid="%s@%s" name='%s' askstatus="-1" recvstatus="-1" substatus="3">\n''' % (item[0], self.domain, item[1]))
                        else:
                            output.write('''     <Item jid="%s@%s" name="%s" askstatus="-1" recvstatus="-1" substatus="3">\n''' % (item[0], self.domain, item[1]))
                else:
                    if(item[1] == ""):
                        output.write('     <Item jid="%s" askstatus="-1" recvstatus="-1" substatus="3">\n' % item[0])
                    else:
                        if ( item[1].find('"') != -1 ):
                            output.write('''     <Item jid="%s" name='%s' askstatus="-1" recvstatus="-1" substatus="3">\n''' % (item[0], item[1]))
                        else:
                            output.write('''     <Item jid="%s" name="%s" askstatus="-1" recvstatus="-1" substatus="3">\n''' % (item[0], item[1]))
                if (item[2] is None):
                    output.write('''      <Group>Buddies</Group>\n''')
                else:
                    output.write('''      <Group>%s</Group>\n''' % item[2])
                output.write('     </Item>\n')
            output.write("    </Roster>\n")

        output.write("  </User>\n")
        #debug ("user <%s> added to the XML file <%s>" % (user['uid'], filename))
        primaryLogger.debug ("user [%s] added to the XML file <%s>" % (user['uid'], filename))

    def xmlFileWrite(self, users, filename):
        """Function to write out the XML file of all the user data"""
        if (filename != ""):
            output = open(filename, "w")
        #debug ("In function xmlFileWrite and opened file <%s> for writting" % filename)
        primaryLogger.debug ("In function xmlFileWrite and opened file <%s> for writting" % filename)

        # print out the header for the XML file
        self.writeXmlHeader(output)
        
        # Loop through the list of dictionaries writing out each users data
        for user in users:
            # skip the ldap_admin user
            if (user['uid'] == "ldap_admin"):
                # we don't want to or need to migrate the ldap_admin account
                continue
            # fix up any passwords that hava an ampersand in them
            if self.containsAny(user['userPassword'], ["&"]):
                debug("replaceing the & in a users password")
                user['userPassword'].replace("&", "&amp;")

            self.writeXmlUser(output, user, filename)

        # print out the footer
        self.writeXmlFooter(output)
        output.close()
        #debug ("file <%s> has been written" % filename)
        primaryLogger.debug ("file <%s> has been written" % filename)
        

    def badRosterUsersGet(self,users):
        """Return a list of user dictionary objects that contain bad roster items"""
        tmpList = list(users)
        badRosterUsers = []
        newRoster = []

        # loop through the users creating a list of users with at least 1 bad roster item
        for user in tmpList:
            if (len(user['roster']) <= 0):
                #if  no roster skip the rest of the loop
                continue
            for roster in user['roster']:
                # -1 means it wasn't found, anything else means it was found
                if ( roster[0].find("\\20") != -1):
                    #debug('found bad roster item "%s"' % roster[0])
                    newRoster.append(roster)
                elif ( roster[0].find("\\27") != -1):
                    newRoster.append(roster)
            # Check to see if we have anything in the roster
            if (len(newRoster) <= 0):
                continue
            else:
                #debug("newRoster is ,%s," % newRoster)
                newUser = user.copy()
                newUser['roster'] = list(newRoster)
                #debug("newUser['roster'] is ,%s," % newUser['roster'])
                badRosterUsers.append(newUser)
                newRoster = []

        return badRosterUsers

    def noRosterUsersGet(self,users):
        """Return a list of all the users with no roster"""
        tmpList = list(users)
        newList = []
        # loop through the users removing the bad roster items
        for user in tmpList:
            if (len(user['roster']) <= 0):
                newList.append(user)

        return newList

    def rosterScrubSpaces(self,users):
        """remove all roster items with a space in them"""
        tmpList = list(users)
        newRoster = []
        newList = []
        # loop through the users removing the bad roster items
        for user in tmpList:
            if (len(user['roster']) <= 0):
                continue
            for roster in user['roster']:
                # -1 means that it wasn't found
                if( roster[0].find("\\20") == -1 ):
                    newRoster.append(roster)
                    #debug ('found good roster item "%s"' % roster[0])
                else:
                    debug('found bad roster item "%s", removing from roster' % roster[0])
                    #pass

            # check to see if we have anything in the roster
            if (len(newRoster) <= 0):
                continue
            else:
                #debug("newRoster is ,%s," % newRoster)
                newUser = user.copy()
                newUser['roster'] = list(newRoster)
                #debug("newUser['roster'] is ,%s," % newUser['roster'])
                newList.append(newUser)
                newRoster = []

        return newList

    def rosterScrubApostrophe(self,users):
        """remove all roster items with a space in them"""
        tmpList = list(users)
        newRoster = []
        newList = []
        # loop through the users removing the bad roster items
        for user in tmpList:
            if (len(user['roster']) <= 0):
                continue
            for roster in user['roster']:
                # -1 means that it wasn't found
                if( roster[0].find("\\27") == -1 ):
                    newRoster.append(roster)
                    #debug ('found good roster item "%s"' % roster[0])
                else:
                    debug('found bad roster item "%s", removing from roster' % roster[0])

            # check to see if we have anything in the roster
            if (len(newRoster) <= 0):
                continue
            else:
                #debug("newRoster is ,%s," % newRoster)
                newUser = user.copy()
                newUser['roster'] = list(newRoster)
                #debug("newUser['roster'] is ,%s," % newUser['roster'])
                newList.append(newUser)
                newRoster = []

        return newList

    def badUsersGet(self,users):
        """ return a list of all the users that have issues with their username"""
        tmpList = list(users)
        newList = []
        # loop through the users removing the bad roster items
        for user in tmpList:
            if ( (self.containsAny(user['uid'], [" "])) or (self.containsAny(user['uid'], ["'"])) ):
                #replace the bad characters and add them to the list
                newUser = user.copy()
                newUser['uid'] = user['uid'].replace(" ", "\\20")
                newUser['uid'] = user['uid'].replace("'", "\\27")
                newList.append(newUser)

        return newList

    def excludeUsersGet(self,users,xlist):
        """ loop through the all the users creating a new list from xlist """
        tmpList = list(users)
        newList = []
        for user in tmpList:
            for name in xlist:
                if (user['uid'] == name):
                    newUser=user.copy()
                    newList.append(newUser)

        return newList

    def exludedUsersRemove(self,users,xlist):
        """ loop through all the users creating a new list that doesn't have any
        users from the xlist in it"""
        tmpList = list(users)
        newList = []
        match = False

        for user in tmpList:
            match = False
            for name in xlist:
                if (user['uid'] == name):
                    match = True
                    break
                else:
                    match = False

            if (match == False):
                newUser=user.copy()
                newList.append(newUser)

        return newList

    def writePwordEmailFile(self,users,filename):
        """loop through the list of users creating a file with EMAIL PASSWORD
        that can be used to send all the users there PASSWORD"""
        if (filename == ""):
            return

        output = open(filename, "w")
        primaryLogger.debug ("In function writePwordEmailFile and opened file <%s> for writting" % filename)

        for user in users:
            output.write("%s %s %s \n" % (user['mail'], user['uid'], user['userPassword']))

        output.close()

    def writeInfoFile(self,users,filename):
        """Loop through the list of users creating a file with the username, name, and email"""
        if (filename == ""):
            return

        output = open(filename, "w")
        primaryLogger.debug ("In function writeInfoFile and opened file <%s> for writting" % filename)

        for user in users:
            output.write("%s,%s,%s\n" % (user['uid'], user['cn'], user['mail']))

        output.close()

def main(argv=None):
    """ The main entry point of the program"""
    if argv is None:
        argv = sys.argv

    global program
    program = argv[0]
    global help_message
    help_message = help_message % (program, program)

    global verbose
    global primaryLogger

    global NOROSTERFILE
    global BADROSTERFILE
    global GOODFILE
    global BADUSERSFILE
    global EXCLUDEFILE
    global LOGFILE
    global EMAIL

    # Setup logging to /dev/null incase no log file is specified
    setupLogging()

    # make sure they are root.  Not sure if I need this check
    if os.getuid() != 0:
        print("YOU MUST BE ROOT TO RUN THIS SCRIPT")
        sys.exit(help_message)

    #print ("len(argv) is ,%s," % len(argv))
    if len(argv) < 1:
        print ("Wrong number of aurguments")
        sys.exit(help_message)

    try:
        try:
            opts, args = getopt.getopt(argv[1:], ":o:l:p:b:r:x:f:mvh", [ "output", "log", "problem", "badroster", "noroster", "exclude", "file", "email", "verbose", "help"])
        except getopt.error, msg:
            raise Usage(msg)

        # option processing
        for option, value in opts:
            #print ("option is ,%s, and value is ,%s," % (option, value))
            if option in ("-v", "verbose"):
                verbose = True
            if option in ("-h", "--help"):
                raise Usage(help_message)
            if option in ("-o", "--output"):
                xmlfile = value
            if option in ("-p", "--problem"):
                problemfile = value
            if option in ("-b", "--badroster"):
                badrosterfile = value
            if option in ("-r", "--noroster"):
                norosterfile = value
            if option in ("-x", "--exclude"):
                excludefilelist = value
            if option in ("-f", "--file"):
                excludefile = value
            if option in ("-l", "--log"):
                logfile = value
                setupLogging(logfile)
                primaryLogger.debug("Logging initiated")
            if option in ("-m", "email"):
                EMAIL = True

        try:
            logfile
        except NameError:
            logfile = LOGFILE
            setupLogging(logfile)
        debug ("Logging initiated with default file ,%s," % logfile)
        primaryLogger.debug("Logging initiated with default file")

        try:
            verbose
        except NameError:
            verbose = False
        debug ("verbose is ,%s," % verbose)
        primaryLogger.debug ("verbose is ,%s," % verbose)

        try:
            xmlfile
        except NameError:
            xmlfile = GOODFILE
        debug ("xmlfile is ,%s," % xmlfile)
        primaryLogger.debug ("xmlfile is ,%s," % xmlfile)

        try:
            problemfile
        except NameError:
            problemfile = BADUSERSFILE
        debug ("problemfile is ,%s," % problemfile)
        primaryLogger.debug ("problemfile is ,%s," % problemfile)

        try:
            badrosterfile
        except NameError:
            badrosterfile = BADROSTERFILE
        debug ("badrosterfile is ,%s," % badrosterfile)
        primaryLogger.debug ("badrosterfile is ,%s," % badrosterfile)

        try:
            norosterfile
        except NameError:
            norosterfile = NOROSTERFILE
        debug ("norosterfile is ,%s," % norosterfile)
        primaryLogger.debug ("norosterfile is ,%s," % norosterfile)

        try:
            excludefilelist
        except NameError:
            excludefilelist = "NOTSET"
        debug ("excludefilelist is ,%s," % excludefilelist)
        primaryLogger.debug ("excludefilelist is ,%s," % excludefilelist)

        try:
            excludefile
        except NameError:
            excludefile = EXCLUDEFILE
        debug ("excludefile is ,%s," % excludefile)
        primaryLogger.debug ("excludefile is ,%s," % excludefile)

        # create an instance of the XcpLDAP class
        l = XcpUsers()
        users = l.allUsersGet()
        primaryLogger.debug("List of users is %s" % users)

        badRosterUsers = l.badRosterUsersGet(users)
        primaryLogger.debug("List of users with at least 1 bad roster item is %s" % badRosterUsers)

        noRosterUsers = l.noRosterUsersGet(users)
        primaryLogger.debug("List of users with no roster is %s" % noRosterUsers)

        badUsers = l.badUsersGet(users)
        primaryLogger.debug("List of users with bad usernames is %s" % badUsers)

        tmpUsers = l.rosterScrubSpaces(users)
        tmp2Users = l.rosterScrubApostrophe(tmpUsers)
        primaryLogger.debug("Users left after removing users with spaces and apostrophes is %s" % tmp2Users)

        if (excludefilelist != "NOTSET" ):
             # open up the excludelist file and populate the list
            handle = open(excludefilelist, 'r')
            excludelist = []
            for line in handle:
                excludelist.append(line.rstrip())
            handle.close()
            debug ("excludelist is ,%s," % excludelist)
            primaryLogger.debug ("excludelist is ,%s," % excludelist)
            
            excludeUsers = l.excludeUsersGet(users,excludelist)
            primaryLogger.debug("List of excluded users is %s" % excludeUsers)
            scrubbedUsers = l.exludedUsersRemove(tmp2Users, excludelist)
            primaryLogger.debug("List of scrubbed users is %s" % scrubbedUsers)
        else:
            scrubbedUsers = tmp2Users
            primaryLogger.debug("List of scrubbed users is %s" % scrubbedUsers)

        # write out the XML files
        l.xmlFileWrite(scrubbedUsers, xmlfile)
        l.xmlFileWrite(badRosterUsers, badrosterfile)
        l.xmlFileWrite(noRosterUsers, norosterfile)
        l.xmlFileWrite(badUsers, problemfile)

        if (excludefilelist != "NOTSET" ):
            l.xmlFileWrite(excludeUsers,excludefile)

        if (EMAIL):
            # write out the user password file(s) to send them emails
            FILENAME = "%s.email" % os.path.splitext(xmlfile)[0]
            l.writePwordEmailFile(scrubbedUsers,FILENAME)
            if (excludefilelist != "NOTSET"):
                FILENAME = "%s.email" % os.path.splitext(excludefile)[0]
                l.writePwordEmailFile(excludeUsers,FILENAME)

        # this is all the users and all the roster items
        l.xmlFileWrite(users, "allUsers.xml")

        # write out the user info of who we are going to migrate
        l.writeInfoFile(scrubbedUsers, "theUserList.txt")
        
        allUsers = l.userNamesGet(users)
        scrubbed = l.userNamesGet(scrubbedUsers)
        noRosters = l.userNamesGet(noRosterUsers)

        handle = open ('allUsers.txt', 'w')
        for item in allUsers:
            handle.write("%s\n" % item)
        handle.close()

        handle = open ('scrubbedUsers.txt', 'w')
        for item in scrubbed:
            handle.write("%s\n" % item)
        handle.close()

        handle = open ('noRosterUsers.txt', 'w')
        for item in noRosters:
            handle.write("%s\n" % item)
        handle.close()
            
    except Usage, err:
        print >> sys.stderr, sys.argv[0].split("/")[-1] + ": " + str(err.msg)
        print >> sys.stderr, "\t for help use --help"
        return 2

if __name__ == "__main__":
    sys.exit(main())
