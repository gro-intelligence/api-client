# Gro API Client
  
## Set up the environment

```sh
mkdir ~/gro
cd ~/gro
git clone https://github.com/gro-intelligence/api-client.git
export PYTHONPATH=~/gro/api-client:$PYTHONPATH
```

Install dependencies (note we're using Python 2.7)

```sh
cd ~/gro/api-client/api/client
pip -r requirements.txt
```

To avoid typing your password on the command line, you can get an API access token as follows:

```sh
cd ~/gro/api-client/api/client
python gro_client.py --user_email='email@example.com' --user_password='securePassword' --print_token
```

To save it in a bash environment variable

```sh
cd ~/gro/api-client/api/client
export GROAPI_TOKEN=`python gro_client.py --user_email=... --user_password=... --print_token`
```

For repeated use, you may want to save PYTHONPATH and GROAPI_TOKEN as permanent environment variables in your bash_profile (or equivalent).

## Examples

Try [quick_start.py](api/client/samples/quick_start.py)

```sh
cd ~/gro/api-client/api/client/samples/
python quick_start.py
```

A more advanced example is [sugar.py](api/client/samples/crop_models/sugar.py)

```sh
cd ~/gro/api-client/api/client/samples/crop_models/
python sugar.py
```

Further documentation can be found in the [api/client/](api/client) directory.