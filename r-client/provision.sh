set -e # exit on any error

echo "Update apt"
sudo DEBIAN_FRONTEND=noninteractive apt-get update -y

echo "Install pip"
sudo apt-get install -y python-pip

echo "Update pip"
sudo -H pip install --upgrade pip

echo "Install virtualenv"
pip install virtualenv

echo "Install R and Rscript"
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
  r-base \
  r-cran-littler

echo "Grant /usr/local/lib/R/site-library ownership to vagrant user"
sudo chown vagrant:vagrant -R /usr/local/lib/R/site-library

# Fix Vagrant on Windows bug with symlinks
# https://github.com/pypa/pipenv/issues/2084
export VIRTUALENV_ALWAYS_COPY=1

echo "Run test script"
Rscript /vagrant/testscript.R
