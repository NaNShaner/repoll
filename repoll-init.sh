#!/bin/bash

############################################################################
# @desc:
#	- 1. create user;
#	- 2. create default directories and authorize;
#	- 3. @usage: sh repoll-init.sh [username]
# @author: NaNShaner
# @time: 191111
###########################################################################

# If the variable is empty, exit
set -o nounset
# Command execution return code is not 0 exit
set -o errexit

readonly redisDir="/opt/repoll/redis"
readonly redisTarGz="redis-3.0.6.tar.gz"


# check if the user exists
checkExist() {
	local num=`cat /etc/passwd | grep -w $1 | wc -l`

	#cat /etc/passwd | grep -q "$1"
	if [[ ${num} == 1 ]]; then
		echo "user $1 exists, overwrite user and *init all data*: [y/n]?"
		read replace
		if [[ ${replace} == "y" ]]; then
			echo "delete existed user: $1."
			userdel -r "$1"
			createUser "$1"
			init "$1"
			return 0
		fi
	else
		createUser "$1"
		init "$1"
	fi
	return 0
}


# create the user
createUser() {
	# create a user
	useradd -m -d /home/$1 -s /bin/bash $1

	# give the user a password
	passwd $1

	#  Maximum number of days between password change
	chage -M 9999 $1
	echo "OK: create user: $1 done"

}

# create defautl dirs and authorize
init() {
	# create working dirs and a tmp dir
	mkdir -p /opt/repoll/data
	mkdir -p /opt/repoll/conf
	mkdir -p /opt/repoll/logs
	mkdir -p /opt/repoll/redis
	mkdir -p /tmp/repoll

	# change owner
	chown -R $1:$1 /opt/repoll
	chown -R $1:$1 /tmp/repoll
	echo "OK: init: $1 done"
}

Get_Dist_Name() {
    if grep -Eqii "CentOS" /etc/issue || grep -Eq "CentOS" /etc/*-release; then
        DISTRO='CentOS'
        PM='yum'
    elif grep -Eqi "Red Hat Enterprise Linux Server" /etc/issue || grep -Eq "Red Hat Enterprise Linux Server" /etc/*-release; then
        DISTRO='RHEL'
        PM='yum'
    elif grep -Eqi "Aliyun" /etc/issue || grep -Eq "Aliyun" /etc/*-release; then
        DISTRO='Aliyun'
        PM='yum'
    elif grep -Eqi "Fedora" /etc/issue || grep -Eq "Fedora" /etc/*-release; then
        DISTRO='Fedora'
        PM='yum'
    elif grep -Eqi "Debian" /etc/issue || grep -Eq "Debian" /etc/*-release; then
        DISTRO='Debian'
        PM='apt'
    elif grep -Eqi "Ubuntu" /etc/issue || grep -Eq "Ubuntu" /etc/*-release; then
        DISTRO='Ubuntu'
        PM='apt'
    elif grep -Eqi "Raspbian" /etc/issue || grep -Eq "Raspbian" /etc/*-release; then
        DISTRO='Raspbian'
        PM='apt'
    else
        DISTRO='unknow'
    fi
    echo $DISTRO;
}

# install redis
installRedis() {
    Get_Dist_Name
	${PM} install -y gcc make
	mkdir -p ${redisDir} && cd ${redisDir}
	wget http://download.redis.io/releases/${redisTarGz} && mv ${redisTarGz} redis.tar.gz && tar zxvf redis.tar.gz --strip-component=1
	make && make install
	if [[ $? == 0 ]]; then
		echo "OK: redis is installed, exit."
		chown -R $1:$1 ${redisDir}
		export PATH=$PATH:${redisDir}/src
		return
	fi
	echo "ERROR: redis is NOT installed, exit."
}

username=$1
checkExist "${username}"
installRedis "${username}"
