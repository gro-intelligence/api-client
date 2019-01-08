# Windows Powershell Setup Instructions

## Prerequisites

1. Download Python version >= 2.7.13 from [python.org](https://www.python.org/downloads/windows/).
2. Install both Python and pip to PATH either in installer (enable component during the installation) or manually. The easiest way to do this is to make sure the below is checked during installation: ![readme_add_python_to_path_installer](readme_add_python_to_path_installer.png)
3. Install Git from [git-scm.com](https://git-scm.com/download/win). Proceed with the default options.

Now, proceed below using Powershell.

## Download the package and CLI

```sh
pip install git+https://github.com/gro-intelligence/api-client.git
```

## Get an authorization token

You can use the gro command line tool to request an authentication token, as in the below example. Note that you will be prompted to enter a password.

```sh
gro --user_email='email@example.com' --print_token
```

In the example code, it is assumed that you have the token saved to your environment variables as GROAPI_TOKEN. You can do that like so:

```sh
$env:GROAPI_TOKEN = "TOKEN_FROM_PREVIOUS_COMMAND"
```

Two notes on authentication tokens:

1. Note that these environment variables *do not persist* when opening new Powershell sessions. For repeated use, you likely want to save GROAPI_TOKEN as a permanent environment variable.
2. Authentication tokens *are subject to expire* though not very often. So if you do save yours elsewhere, you can add robustness to your application by falling back to api.client.lib.get_access_token() to get a new one if your previous one has expired.