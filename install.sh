#!/bin/bash
echo "Beginning installation..."

cleanup() {
    rv=$?
    rm -rf "~/.firecloud-cli"
    echo
    echo "------------------------------"
    echo "ERROR... aborting installation"
    echo "------------------------------"
    exit $rv
}

trap "cleanup" INT TERM EXIT

rm -rf ~/.firecloud-cli
mkdir -p ~/.firecloud-cli
echo "Creating Python virtual environment"
virtualenv -q ~/.firecloud-cli/venv
echo "Installing Firecloud CLI"
source ~/.firecloud-cli/venv/bin/activate
python setup.py -q install &> ~/.firecloud-cli/install.log
deactivate
echo "Linking binaries "
mkdir -p ~/.firecloud-cli/ubin
ln -s ~/.firecloud-cli/venv/bin/agora ~/.firecloud-cli/ubin
ln -s ~/.firecloud-cli/venv/bin/firecloud ~/.firecloud-cli/ubin

trap - INT TERM EXIT

echo "Firecloud CLI has been installed in ~/.firecloud-cli/venv/bin"
echo
echo "You may want to include this in your default path by adding "
echo "the following to your .bashrc, .bash_profile or equivalent  "
echo
echo "   export PATH=~/.firecloud-cli/ubin:\$PATH"