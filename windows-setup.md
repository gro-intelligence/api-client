# Windows Powershell Setup Instructions

## Prerequisites

1. Download Python version >= 2.7.13 from [python.org](https://www.python.org/downloads/windows/).
2. Install both Python and pip to PATH either in installer (enable component during the installation) or manually. The easiest way to do this is to make sure the below is checked during installation: ![readme_add_python_to_path_installer](readme_add_python_to_path_installer.png)
3. Install Git from [git-scm.com](https://git-scm.com/download/win). Proceed with the default options.

Now, proceed below using Powershell.

## Clone the library

```sh
mkdir ~/gro

cd ~/gro

git clone https://github.com/gro-intelligence/api-client.git
```

## Add the library to PYTHONPATH

```sh
$env:PYTHONPATH = "$env:USERPROFILE\gro\api-client;$env:PYTHONPATH"
```

## Install dependencies

Note these requirements are for the sample code. You may need more or fewer for your specific application.

```sh
cd ~/gro/api-client/api/client

pip install -r requirements.txt
```

## Get an authorization token

```sh
cd ~/gro/api-client/api/client

python gro_client.py --user_email='email@example.com'  --print_token
```

Copy and paste this token into this command

```sh
$env:GROAPI_TOKEN = "TOKEN_FROM_PREVIOUS_COMMAND"
```

Note that these environment variables *do not persist* when opening new Powershell sessions. For repeated use, you likely want to save PYTHONPATH and GROAPI_TOKEN as permanent environment variables.