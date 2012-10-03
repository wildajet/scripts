#!/usr/bin/perl
#
# Author:               Jet Wilda <jet.wilda@gmail.com>
# Modifed by:           Jet Wilda <jet.wilda@gmail.com>
# Last Modified:        10/02/2012
#
# Description:
#       Script to update the SNMP mailstats
#
# this was created from http://community.zenoss.org/docs/DOC-2477
# which modified the script from http://taz.net.au/postfix/mrtg/
#
# On CentOS 5 you need to install the perl-File-Tail package.  The easiest way to do that
# is to install RPMForge i.e. http://www.ultranetsolutions.com/CentOS-5-install-rpmforge-yum-repo.html
# and then do yum -y install perl-File-Tail
#

use DB_File;
use File::Tail;
$debug = 0;

$mail_log = '/var/log/maillog';
$stats_file = '/tmp/stats.db';

$db = tie(%stats, "DB_File", "$stats_file", O_CREAT|O_RDWR, 0666, $DB_HASH)
        || die ("Cannot open $stats_file");

#my $logref=tie(*LOG,"File::Tail",(name=>$mail_log,tail=>-1,debug=>$debug));
my $logref=tie(*LOG,"File::Tail",(name=>$mail_log,debug=>$debug));

while (<LOG>) {
        if (/status=sent/) {
                next unless (/ postfix\//);
                # count sent messages
                if (/relay=([^,]+)/o) {
                        $relay = $1;
                        #print "$relay...";
                } ;
                if ($relay !~ /\[/o ) {
                        $stats{"SENT:$relay"} += 1;
                        #print "$relay\n";
                } else {
                        $stats{"SENT:smtp"} +=1;
                        #print "smtp\n" ;
                } ;
                $db->sync;
        } elsif (/status=bounced/) {
                # count bounced messages
                $stats{"BOUNCED:smtp"} += 1;
                $db->sync ;
        } elsif (/NOQUEUE: reject/) {
                # count rejected messages
                $stats{"REJECTED:smtp"} += 1;
                $db->sync ;
        } elsif (/smtpd.*client=/) {
                # count received smtp messages
                $stats{"RECEIVED:smtp"} += 1;
                $db->sync ;
        } elsif (/pickup.*(sender|uid)=/) {
                # count received local messages
                $stats{"RECEIVED:local"} += 1;
                $db->sync ;
        } ;
} ;

untie $logref ;
untie %stats;
