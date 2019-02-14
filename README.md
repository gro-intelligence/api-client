# Gro API Client

https://www.gro-intelligence.com/products/gro-api

Client library for accessing Gro Intelligence's agriculture data platform.

## Setup

1. [MacOS and Linux](unix-setup.md)
2. [Windows](windows-setup.md)

## Examples

Download or clone this repository, and then you can navigate to our [api/client/samples/](api/client/samples/) folder and try executing the provided examples.

Try [quick_start.py](api/client/samples/quick_start.py)

```sh
cd your-clone-path/api-client/api/client/samples/

python quick_start.py
```

Now should be able to find a sample output csv file at:

```sh
your-clone-path/api-client/api/client/samples/gro_client_output.csv
```

You can also use the Gro CLI as a quick and easy way to request a single data series right on the command line. You can either provide your email and enter a password when prompted, or you can provide your --token to avoid typing a password every time:

```sh
gro --metric='Production Quantity mass' --item='Corn' --region='United States' --user_email='email@expample.com'
Password: <enter password when prompted>

or

gro --metric='Production Quantity mass' --item='Corn' --region='United States' --token='token-generated-in-setup-steps'
```

This will choose the first matching data series and output the results to a gro_client_output.csv file in your current directory.

Further documentation can be found in the [api/client/](api/client) directory and on our [wiki](https://github.com/gro-intelligence/api-client/wiki).
