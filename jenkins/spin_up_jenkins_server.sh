#!/bin/bash
set -e
set -v


# modifiable setings
cluster_name=$1
local_crosscat_dir=$2
# fall back to defaults
if [[ -z $cluster_name ]]; then
	cluster_name=crosscat
fi
if [[ -z $local_crosscat_dir ]]; then
	local_crosscat_dir=/opt/crosscat
fi
# set derived variables
local_jenkins_dir=$local_crosscat_dir/jenkins


# spin up the cluster
starcluster start -c crosscat -i c1.xlarge -s 1 $cluster_name
hostname=$(starcluster listclusters $cluster_name | grep master | awk '{print $NF}')


# open up the port for jenkins
open_port_script=$local_jenkins_dir/open_master_port_via_starcluster_shell.py
starcluster shell < <(perl -pe "s/'crosscat'/'$cluster_name'/" $open_port_script)


# bypass key checking
ssh -o PasswordAuthentication=no -o StrictHostKeyChecking=no jenkins@$hostname exit || true
# set up jenkins: RELIES ON CODE BEING IN /root/crosscat
starcluster sshmaster $cluster_name "(cd crosscat && git pull)"
starcluster sshmaster $cluster_name bash crosscat/jenkins/setup_jenkins.sh


# push up jenkins configuration
# jenkins server must be up and ready
jenkins_uri=http://$hostname:8080
jenkins_utils_script=$local_jenkins_dir/jenkins_utils.py
config_filename=$local_jenkins_dir/config.xml
python $jenkins_utils_script \
	--base_url $jenkins_uri \
	--config_filename $config_filename \
	-create


# notify user what hostname is
echo $hostname
