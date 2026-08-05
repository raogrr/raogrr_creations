#! /bin/bash
# Author - Gururaj Rao
# Works for centrify user and local user to build and install custom python3.9.xx, by default, it will install python3.9.11
# This script compatible for ubuntu 16.04, 18.04, 20.04 and 22.04

help()
{
    echo "Usage: custom_python3_build_install.sh [ -v | --version| --VERSION ]
               [ -h | --help  ]
          Example: dzdo bash custom_python3_build_install.sh -v 3.9.13"
    exit 0
}

error_exit() {
    echo -e "ERROR:$@"
    exit 2

}

SHORT=v:,h
LONG=version:,VERSION:,help
OPTS=$(getopt -a -n custom_python3_build_install.sh --options $SHORT --longoptions $LONG -- "$@")

VALID_ARGUMENTS=$# # Returns the count of arguments that are in short or long options

eval set -- "$OPTS"


while :
do
  case "$1" in
    -v | --version| --VERSION)
      VERSION=$2
      echo -e "VERSION:$VERSION\n"
      shift 2
      ;;
    -h | --help)
      help
      ;;
    --)
      shift;
      break
      ;;
    *)
      echo "Unexpected option: $1"
      help
      ;;
  esac
done

[[ -z ${VERSION} ]] && VERSION="3.9.11" && echo -e "VERSION:${VERSION}\n"


has_sudo() {

    local prompt
    username=$(whoami||adquery user ${USER} -n)
    prompt=$(sudo -nv 2>&1||getent group sudo|grep -i $username)
    if [ $? -eq 0 ]; then
       echo "has_sudo_access_pass_set"
    elif echo $prompt | grep -q '^sudo:'; then
       echo "has_sudo_access_needs_pass"
    else
       echo "no_sudo_access_need_centrify_dzdo"
    fi
}

if [[ $(has_sudo) =~ "has_sudo_access" ]]; then
   PRIV_USER=sudo
else
   echo -e "Use dzdo command"
   PRIV_USER=dzdo
fi

UBUNTU_RELEASE=$(lsb_release -r|awk -F: '{print $2}'|tr -d "[:blank:]")
echo -e "UBUNTU_RELEASE:${UBUNTU_RELEASE}\n"
#Custom python3.9.11 building and installation
if [[ "${UBUNTU_RELEASE}" != "22.04" ]]; then
   ${PRIV_USER} apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
   libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
   xz-utils tk-dev libffi-dev liblzma-dev python-openssl git || error_exit "\nUnable to execute apt update\n"
else
   ${PRIV_USER} apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
   libreadline-dev libsqlite3-dev wget curl llvm libncurses5-dev libncursesw5-dev \
   xz-utils tk-dev libffi-dev liblzma-dev  git || error_exit "\nUnable to execute apt update\n"
fi
[[ -n /opt/python-${VERSION} ]] && ${PRIV_USER} rm -rf /opt/python-* && pwd
${PRIV_USER} mkdir -p /opt/python-${VERSION} && cd /opt/python-${VERSION}
[[ "$?" == "0" ]] && ${PRIV_USER} wget https://www.python.org/ftp/python/${VERSION}/Python-${VERSION}.tgz || error_exit "\n Unable to download python-${VERSION}.tgz in /opt location"
${PRIV_USER} tar -xf Python-${VERSION}.tgz && cd Python-${VERSION}
${PRIV_USER} ./configure --enable-optimizations && ${PRIV_USER} make -j 8 && ${PRIV_USER} make altinstall
cd .. && ${PRIV_USER} rm -rf Python-${VERSION}.tgz Python-${VERSION}


# post installations - configure python3 to use customized python without disturbing OS level python located in /usr/bin
cd /usr/local/bin && \
[[ ! -L python3 ]] && [[ ! -e python3 ]] && ${PRIV_USER} ln -s python3.9 python3 && \
[[ ! -L python3-config ]] && [[ ! -e python3-config ]] && ${PRIV_USER} ln -s python3.9-config python3-config &&  \
[[ ! -L pip3 ]] && [[ ! -e pip3 ]] && ${PRIV_USER} ln -s pip3.9 pip3 && \
[[ ! -L 2to3 ]] && [[ ! -e 2to3 ]] && ${PRIV_USER} ln -s 2to3-3.9 2to3 && \
[[ ! -L idle3 ]] && [[ ! -e idle3 ]] && ${PRIV_USER} ln -s idle3.9 idle3 && \
[[ ! -L pydoc3 ]] && [[ ! -e pydoc3 ]] && ${PRIV_USER} ln -s pydoc3.9 pydoc3 && \
cd /usr/bin && [[ ! -f python3 ]] && ${PRIV_USER} rm -f python3
 
#Set the custom python installed path
egrep -R 'export PATH=/usr/local/bin:' ${HOME}/.bashrc
[[ "$?" == "0" ]] && echo "PATH is already set" || echo 'export PATH=/usr/local/bin:${PATH}' >> ${HOME}/.bashrc
source ${HOME}/.bashrc