# Gro API Client

https://www.gro-intelligence.com/products/gro-api

Client library for accessing Gro Intelligence's agricultural data platform.

## Prerequisites

1. [MacOS and Linux](unix-setup.md)
2. [Windows](windows-setup.md)

## Install Gro API client packages

There are two installation methods: using pip, or using git. 

### Install with pip install (preferred)

```sh
pip install git+https://github.com/gro-intelligence/api-client.git [--target=<your-gro-path>]
```

If you don't specify your gro installation path, it will be the local [site-packages]( https://stackoverflow.com/questions/31384639/what-is-pythons-site-packages-directory) directory.

### Install with git clone 

```
git clone https://github.com/gro-intelligence/api-client.git  [<your-gro-path>]
```
If you don't specify your gro installation path, it will be the current directory.
In addition, optionally you can:

1. [Set `PYTHONPATH=<your-gro-path>` as an environment variable] (https://www.techwalla.com/articles/how-to-set-your-python-path)

2. Make `gro_client` an alias for `python <your-gro-path>/gro_client.py`


## Gro API authentication token

### Getting a token

You can use the gro_client command line tool to request an authentication token. Note that you will be prompted to enter a password.

```sh
gro_client --user_email='email@example.com' --print_token
```

This token is used throughout wherever authentication is required.

### Saving your token as an environment variable

If you don't want to enter a password or token each time, you can save
the token as an environment variable. In the sample code, it is
assumed that you have the token saved to your environment variables as
GROAPI_TOKEN.

Note that Gro authentication tokens *are subject to expire* though not
very often. So if you do save yours elsewhere, you can add robustness
to your application by falling back to
`api.client.lib.get_access_token()` to get a new one if your previous
one has expired.

## Examples

Navigate to [api/client/samples/](api/client/samples/) folder and try executing the provided examples.

Try [quick_start.py](api/client/samples/quick_start.py)

```sh
cd your-gro-path/api-client/api/client/samples/

python quick_start.py
```
Now should be able to find a sample output csv file at: `gro_client_output.csv`

A more advanced example is [sugar.py](api/client/samples/crop_models/sugar.py)

```sh
cd your-gro-path/api-client/api/client/samples/crop_models/
python sugar.py
```

You can also use the Gro CLI as a quick and easy way to request a single data series right on the command line. You can either provide your email and enter a password when prompted, or you can provide your --token to avoid typing a password every time:

```sh
gro_client --metric='Production Quantity mass' --item='Corn' --region='United States' --user_email='email@expample.com'
Password: <enter password when prompted>

or

gro_client --metric='Production Quantity mass' --item='Corn' --region='United States' --token='token-generated-in-setup-steps'
```

This will choose the first matching data series and output the results to a `gro_client_output.csv` file in your current directory.

Further documentation can be found in the [api/client/](api/client) directory and on our [wiki](https://github.com/gro-intelligence/api-client/wiki).
