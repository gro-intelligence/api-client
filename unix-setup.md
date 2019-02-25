# MacOS and Linux Setup Instrutions

## Prerequisite

1. git ([Installation instructions](https://git-scm.com/book/en/v2/Getting-Started-Installing-Git))
2. python (2.7.x or 3.x) ([2 Installation instructions](https://docs.python.org/2/using/index.html) / [3 Installation instructions](https://docs.python.org/3/using/index.html))
3. pip ([Installation instructions](https://pip.pypa.io/en/stable/installing/). Note "pip is already installed if you are using Python 2 >=2.7.9 or Python 3 >=3.4")

## Install the packages

There are two standard installation methods: using pip, or using git. 

### Install with pip install

```sh
pip install git+https://github.com/gro-intelligence/api-client.git --target=<your-gro-path>
```

If you don't specify the your gro installation path, it will be in the local [site-packages]( https://stackoverflow.com/questions/31384639/what-is-pythons-site-packages-directory) directory.

### Install with git clone

```
git clone https://github.com/gro-intelligence/api-client.git  [<your-gro-path>]
```
Edit your .bash_profile (or equivalent) and add the following line 
```export PYTHONPATH=<your-gro-path>:$PYTHONPATH```

## Get an authorization token

You can use the gro_client command line tool to request an authentication token, as in the below example. Note that you will be prompted to enter a password.

```sh
gro_client --user_email='email@example.com' --print_token
```

## Save Gro API token as an environment variable

In the sample code, it is assumed that you have the token saved to your environment variables as GROAPI_TOKEN.  Take the output of the --print_token and save it by adding a line in your .bash_profile (or equivalent) like the following:

```
export GROAPI_TOKEN=<output of gro_client print_token command>
```

Note that Gro authentication tokens *are subject to expire* though not very often. So if you do save yours elsewhere, you can add robustness to your application by falling back to api.client.lib.get_access_token() to get a new one if your previous one has expired.
