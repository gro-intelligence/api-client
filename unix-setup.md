# MacOS and Linux Setup Instrutions

## Prerequisites

1. git ([Installation instructions](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))
2. python (2.7.x or 3.x) ([2 Installation instructions](https://docs.python.org/2/using/index.html) / [3 Installation instructions](https://docs.python.org/3/using/index.html))
3. pip ([Installation instructions](https://pip.pypa.io/en/stable/installing/). Note "pip is already installed if you are using Python 2 >=2.7.9 or Python 3 >=3.4")

## Install the package and CLI

```sh
pip install git+https://github.com/gro-intelligence/api-client.git
```

## Get an authorization token

You can use the gro_client command line tool to request an authentication token, as in the below example. Note that you will be prompted to enter a password.

```sh
gro_client --user_email='email@example.com' --print_token
```

In the example code, it is assumed that you have the token saved to your environment variables as GROAPI_TOKEN. You can do this in one line like so:

```sh
export GROAPI_TOKEN=`gro_client --user_email='email@example.com' --print_token`
```

Two notes on authentication tokens:

1. Note that bash environment variables *do not persist* when opening new shell sessions. For repeated use, you likely want to save your GROAPI_TOKEN as permanent environment variable in your bash_profile (or equivalent).
2. Authentication tokens *are subject to expire* though not very often. So if you do save yours elsewhere, you can add robustness to your application by falling back to api.client.lib.get_access_token() to get a new one if your previous one has expired.