#!/usr/bin/perl
#
# Author:               Jet Wilda <jet.wilda@gmail.com>
# Modifed by:           Jet Wilda <jet.wilda@gmail.com>
# Last Modified:        10/02/2012
#
# Description:
#       Script to create mail stats for SNMP
#
# this was created from http://community.zenoss.org/docs/DOC-2477
# which modified the script from http://taz.net.au/postfix/mrtg/
#

use DB_File;
$NOTFOUND=0;
$LOCAL=0;
$SMTP=0;
$TOTAL=0;
$RECEIVED=0;
$BOUNCED=0;
$REJECTED=0;
$QUEUE=0;

$|=1;

$stats_file = '/tmp/stats.db' ;

tie(%foo, "DB_File", "$stats_file", O_RDONLY, 0666, $DB_HASH) || die ("Cannot open $stats_file");

if ($ARGV[0] =~ /sent/) {
    foreach (sort keys %foo) {
        #print " _ is ,$_, and foo{_} is ,$foo{$_}, \n";
        if ( $_ =~ /SENT:smtp/ ) {
            if ( $foo{$_} =~ /^-?\d/ ) {
                $SMTP = $foo{$_};
            } else {
                $SMTP = 0;
            }
        } elsif ( $_ =~ /SENT:local/ ) {
            if ( $foo{$_} =~ /^-?\d/ ) {
                $LOCAL = $foo{$_};
            } else {
                $LOCAL = 0;
            } 
        }
    }
    $TOTAL = $SMTP + $LOCAL;
    print $TOTAL;
} elsif ($ARGV[0] =~ /received/) {
    foreach (sort keys %foo) {
        if ( $_ =~ /RECEIVED/ ) {
            if ( $foo{$_} =~ /^-?\d/ ) {
                $RECEIVED = $foo{$_};
            } else {
                $RECEIVED = 0;
            }
        } 
    }
    print $RECEIVED;
} elsif ($ARGV[0] =~ /bounced/) {
    foreach (sort keys %foo) {
        if ( $_ =~ /BOUNCED/ ) {
            if ( $foo{$_} =~ /^-?\d/ ) {
                $BOUNCED = $foo{$_};
            } else {
                $BOUNCED = 0;
            }
        } 
    }
    print $BOUNCED;
} elsif ($ARGV[0] =~ /rejected/) {
    foreach (sort keys %foo) {
        if ( $_ =~ /REJECTED/ ) {
            if ( $foo{$_} =~ /^-?\d/ ) {
                $REJECTED = $foo{$_};
            } else {
                $REJECTED = 0;
            }
        } 
    }
    print $REJECTED;
} elsif ($ARGV[0] =~ /queue/) {
    @mailq = split(/\n/,`postqueue -p`);
    #print "mailq is ,@mailq,\n"; }
    #foreach $item (@mailq) { print "item is ,$item,\n"; }
    #print "size is ,$#mailq,\n";
    @line = split(' ',$mailq[$#mailq]);
    #foreach (@line){ print ",$_,\n"; }
    #print "line size is ,$#line,\n";
    #print "line[3] is ,$line[3],\n";
    #print "line[4] is ,$line[4],\n";
    if ( $line[4] =~ /^-?\d/) {
      $QUEUE = $line[4];
    } else {
      $QUEUE = 0;
    }
    print $QUEUE;
}
untie %foo;
