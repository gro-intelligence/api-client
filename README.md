# Gro api-client
Gro Intelligence API Client
  
Set up the environment:
```
cd ~/gro
git clone https://github.com/gro-intelligence/api-client.git
export PYTHONPATH=~/gro:$PYTHONPATH
```

To avoid typing your password on the command line, you can get an API access token as follows:

```
cd ~/gro/api/client
python gro_client.py --user_email=... --user_password=.... --print_token
```

To save it in a bash environment variable:
                                                                                                                                                                               
```
export GROAPI_TOKEN=`python gro_client.py --user_email=... --user_password=... --print_token`
```

Run an example

```
cd ~/gro/api/client/samples/crop_models/
python sugar.py
```

