<p align="center"><img width=8% src="https://gro-intelligence.com/images/logo.jpg"></p>

# Gro API Client

https://www.gro-intelligence.com/products/gro-api

Client library for accessing Gro Intelligence's agricultural data platform.

## Prerequisites

1. [MacOS and Linux](unix-setup.md)
2. [Windows](windows-setup.md)

## Install Gro API client packages

```sh
pip install git+https://github.com/gro-intelligence/api-client.git
```

## Gro API authentication token

Use the Gro web application to retrieve an authentication token (instructions are in the wiki [here](https://github.com/gro-intelligence/api-client/wiki/Authentication-Tokens#11-using-the-gro-web-application-preferred)).

### Saving your token as an environment variable (optional)

If you don't want to enter a password or token each time, you can save the token as an environment variable. Please consult your OS or IDE documentation for information on how to set environment variables, e.g. [setting environment variables in Windows Powershell](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-6) and [Mac OS X/Linux](https://apple.stackexchange.com/questions/106778/how-do-i-set-environment-variables-on-os-x). In some of the sample code, it is assumed that you have the token saved to your environment variables as `GROAPI_TOKEN`.

## Examples

Navigate to [api/client/samples/](api/client/samples/) folder and try executing the provided examples.

1. Try [quick_start.py](api/client/samples/quick_start.py).

```sh
python quick_start.py
```

If the API client is installed and your authentication token is set, a csv file called `gro_client_output.csv` should be created in the directory where the script was run.

2. Try out [soybeans.py](api/client/samples/crop_models/soybeans.py) to see the crop weighted series feature in action:

```sh
python crop_models/soybeans.py
```

3. See [brazil_soybeans.ipynb](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/crop_models/brazil_soybeans.ipynb) for a longer, more detailed demonstration of many of the API's capabilities in a Jupyter notebook.

Further documentation can be found in the [api/client/](api/client) directory and on our [wiki](https://github.com/gro-intelligence/api-client/wiki).
