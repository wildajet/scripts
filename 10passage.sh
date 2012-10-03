#!/bin/bash
#
# Author:               Rob Owens <doomicon@gmail.com>
# Modifed by:           Jet Wilda <jet.wilda@gmail.com>
# Last Modified:        10/03/2012
#
# Description:
#  Script to check when users passwords expire and email them letting them know.
#

HOSTNAME=`hostname`
LOGFILE=/tmp/passage.out

if [ -f $LOGFILE ]
        then rm $LOGFILE
fi

DATE=`date +%m%d%y` > $LOGFILE
echo "#$HOSTNAME:$DATE" >> $LOGFILE

echo "Please login to change your password prior to expiration." > $LOGFILE
MailBody=$LOGFILE

declare -a users=(`cat /etc/shadow | grep -v ':!!:' | grep -v :99999: | cut -d: -f1`)

for USER in ${users[*]}
do
	CURRENT_EPOCH=`grep ^$USER: /etc/shadow | cut -d: -f3`
	EMAIL=`grep ^$USER /etc/passwd | cut -d: -f5`

	# Find the epoch time since the user's password was last changed
	#EPOCH=`/usr/bin/perl -e 'print int(time/(60*60*24))'`
	let EPOCH=`date +%s`/86400
	# Compute the age of the user's password
	AGE=`echo $EPOCH - $CURRENT_EPOCH | /usr/bin/bc`

	# Compute and display the number of days until password expiration
	MAX=`grep ^$USER: /etc/shadow | cut -d: -f5`
	EXPIRE=`echo $MAX - $AGE | /usr/bin/bc`

	CHANGE=`echo $CURRENT_EPOCH + 1 | /usr/bin/bc`
	LSTCNG="`perl -e 'print scalar localtime('$CHANGE' * 24 *3600);'`"
	if [ "$EXPIRE" -lt 14 ] && [ "$EXPIRE" -gt 0 ]
	then
        echo -e "Hi $USER,\n\n\tPlease login to change your password prior to expiration.\n\n${USER}'s password will expire in $EXPIRE days\n\nPASSWORD EXPERATION DETAILS:\n\n `chage -l $USER`\n\nThanks,\nYour friendly neighborhood Unix Admin :-)" | mail -s "$HOSTNAME: Password expire in $EXPIRE days" $EMAIL
	fi
done

if [ -f $MailBody ]
        then rm $MailBody
fi
