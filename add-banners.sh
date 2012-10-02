#!/bin/bash
#
# Author: 		Jet Wilda <jet.wilda@gmail.com>
# Modifed by:		Jet Wilda <jet.wilda@gmail.com>
# Last Modified: 	10/02/2012
#
# Description:
#	Script to create banner files that can be displayed as Warnings For Network And Physical Access Services
#

echo "Create Warnings For Network And Physical Access Services"
echo

#unalias cp mv
cd /etc

for FILE in issue issue.net; do

echo "***************************************************************************" >> ${FILE}.tmp
echo "                            NOTICE TO USERS" >> ${FILE}.tmp
echo "" >> ${FILE}.tmp
echo "This computer system is private property, whether" >> ${FILE}.tmp
echo "individual, corporate or government.  It is for authorized use only." >> ${FILE}.tmp
echo "Users (authorized or unauthorized) have no explicit or implicit" >> ${FILE}.tmp
echo "expectation of privacy." >> ${FILE}.tmp
echo "" >> ${FILE}.tmp
echo "Any or all uses of this system and all files on this system may be" >> ${FILE}.tmp
echo "intercepted, monitored, recorded, copied, audited, inspected, and" >> ${FILE}.tmp
echo "disclosed to your employer, to authorized site, government, and law" >> ${FILE}.tmp
echo "enforcement personnel, as well as authorized officials of government" >> ${FILE}.tmp
echo "agencies, both domestic and foreign." >> ${FILE}.tmp
echo "" >> ${FILE}.tmp
echo "By using this system, the user consents to such interception, monitoring," >> ${FILE}.tmp
echo "recording, copying, auditing, inspection, and disclosure at the" >> ${FILE}.tmp
echo "discretion of such personnel or officials.  Unauthorized or improper use" >> ${FILE}.tmp
echo "of this system may result in civil and criminal penalties and" >> ${FILE}.tmp
echo "administrative or disciplinary action, as appropriate. By continuing to use" >> ${FILE}.tmp
echo "this system you indicate your awareness of and consent to these terms" >> ${FILE}.tmp
echo "and conditions of use. LOG OFF IMMEDIATELY if you do not agree to the" >> ${FILE}.tmp
echo "conditions stated in this warning." >> ${FILE}.tmp
echo "" >> ${FILE}.tmp
echo "****************************************************************************" >> ${FILE}.tmp

mv ${FILE}.tmp ${FILE}
done

echo "" >> motd.tmp
echo "***************************************************************************" >> motd.tmp
echo "                            NOTICE TO USERS" >> motd.tmp
echo "" >> motd.tmp
echo "Authorized uses only. All activity may be monitored and reported." >> motd.tmp
echo "" >> motd.tmp
echo "****************************************************************************" >> motd.tmp

mv motd.tmp motd

chown root:root /etc/motd /etc/issue /etc/issue.net
chmod 644 /etc/motd /etc/issue /etc/issue.net

echo
echo -e "\033[1m***   \033[1;31mFinished creating Warnings For Network And Physical Access Services.  You may want to edit /etc/ssh/sshd_config so it uses these new banner files!\033[0m\033[1m   ***\033[0m"
echo
