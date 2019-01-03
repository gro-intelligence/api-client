# MacOS and Linux Setup Instrutions

## Prerequisites

1. git ([Installation instructions](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))
2. python (2.7.x or 3.x) ([2 Installation instructions](https://docs.python.org/2/using/index.html) / [3 Installation instructions](https://docs.python.org/3/using/index.html))
3. pip ([Installation instructions](https://pip.pypa.io/en/stable/installing/). Note "pip is already installed if you are using Python 2 >=2.7.9 or Python 3 >=3.4")

## Clone the library

```sh
mkdir ~/gro

cd ~/gro

git clone https://github.com/gro-intelligence/api-client.git
```

## Add the library to PYTHONPATH

```sh
export PYTHONPATH=~/gro/api-client:$PYTHONPATH
```

## Install dependencies

Note these requirements are for the sample code. You may need more or fewer for your specific application.

```sh
cd ~/gro/api-client/api/client

pip install -r requirements.txt
```

## Get an authorization token

To save an API access token into a bash environment variable

```sh
cd ~/gro/api-client/api/client

export GROAPI_TOKEN=`python gro_client.py --user_email='email@example.com' --user_password='securePassword' --print_token`
```

Note that these environment variables *do not persist* when opening new shell sessions. For repeated use, you likely want to save PYTHONPATH and GROAPI_TOKEN as permanent environment variables in your bash_profile (or equivalent).