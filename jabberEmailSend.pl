#!/usr/bin/perl -w
#
# Author:               Jet Wilda <jet.wilda@gmail.com>
# Modifed by:           Jet Wilda <jet.wilda@gmail.com>
# Last Modified:        10/02/2012
#
# Description:
#       Loop through a a file that has 3 items on each line space seperated
#       The first item on each line is the email address.  Email the other 2 items
#


use Getopt::Long;
#use strict;
use warnings;

# configure GetOptions to accept short and long paramaters
Getopt::Long::Configure ('bundling');

my $DEBUG = '';
my $PFROM = q/"FROM NAME"/;
my $FROM = q/"FROM EMAIL "/;
my $SUBJECT = q/"DO NOT DELETE:  Important IT Message!"/;

sub debug
{
   my $data = $_[0];
   if ( $DEBUG ne '' ){
      print ( $data );
   }
}

sub usage
{
 print ("\n$0 -f FILE \n");
 print ("\t-f|--file           # file that has users to either check for or inactivate [one per line]\n");
 print ("\t-v|--verbose        # print out all kinds of debug messages\n");
 print ("\t-h|--help           # Display this help message \n");
 print ("\ni.e.\n  $0 -f data.email \n\n");
}

my ($FILE, $HELP);

GetOptions ("f|file=s" => \$FILE, "v|verbose" => \$DEBUG, "h|help" => \$HELP);

#check if they want help
if ( defined ($HELP) ) {
    usage;
    exit;
}

if ( ! defined ($FILE) ) {
 print ("\n ERROR you must specify the FILE to be used with the -f option\n");
 usage;
 exit;
}
debug ("File is $FILE\n");

open (HANDLE, $FILE) || die ("Unable to open $FILE: $!");
debug ("$FILE opened\n");

foreach $line (<HANDLE>) {
	my ($email, $uid, $pass) = split (/ /, $line);
        my $MESSAGE = "Hi,\n\n\tThis email contains your current Jabber Instant Messenger Login information that you will use for the new Spark Instant Messenger Client.\n\n\tusername:\t$uid\n\tpassword:\t$pass\n\nWhat do I do now?\n\n\t1.\tOpen the Spark IM Client under Start/Programs";
	my $cmd = "echo -e \"$MESSAGE\" | mail -s $SUBJECT $email -- -F $PFROM -f $FROM";
	`$cmd`;
	debug ("executed:\n\t$cmd\n");
}
