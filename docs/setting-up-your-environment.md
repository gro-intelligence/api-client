# Setting Up Your Environment

In order to start engaging with the Gro API Client, you will need to set up your local environment with some basic requirements.

1. [System Prerequisites](#system-prerequisites)
2. [Authentication Token/Saving Environment Variables](#authentication-token)

## System Prerequisites

The Gro API Client requires the following OS-dependant system requirements.

### MacOS and Linux

1. git (Installation instructions)
2. python (2.7.x or 3.x) (2 Installation instructions / 3 Installation instructions)
3. pip (Installation instructions. Note "pip is already installed if you are using Python 2 >=2.7.9 or Python 3 >=3.4")

### Windows

The Gro API Client package is supported both with or without Anaconda. However, some popular data science packages, including some used in the sample scripts provided, are only available on Windows via [conda](https://docs.conda.io/en/latest/). For that reason, instructions are provided for both. You should select the distribution that fits your requirements.

Anaconda
1. Download Anaconda with Python 3.5 or above from [anaconda.com](https://www.anaconda.com/distribution/). Support for Python 2.7.13 or above is also maintained, but with [its End of Life](https://mail.python.org/pipermail/python-dev/2018-March/152348.html) soon approaching, it is recommended you start with Python 3.
2. Install Git from [git-scm.com](https://git-scm.com/download/win). Proceed with the default options.

Non-Anaconda
1. Powershell (should come default with Windows) 
2. Download Python version 3.5 or above from [python.org](https://www.python.org/downloads/windows/). Support for Python 2.7.13 or above is also maintained, but with [its End of Life](https://mail.python.org/pipermail/python-dev/2018-March/152348.html) soon approaching, it is recommended you start with Python 3.
3. Install both Python and pip to PATH either in the installer (enable component during the installation) or manually. The easiest way to do this is to make sure the below is checked during installation: ![readme_add_python_to_path_installer](readme_add_python_to_path_installer.png)
4. Install Git from [git-scm.com](https://git-scm.com/download/win). Proceed with the default options.


### Python

The Gro API client is compatible with both Python 2.7.x and Python 3.x (3.6 and 3.7 are currently tested). 

### Installing Gro Packages

Now that you have downloaded the base system requirements, you will need to install the packages for the Gro API Client.

Install with pip install

```
pip install git+https://github.com/gro-intelligence/api-client.git
```
Note: even if you are using [Anaconda](https://www.anaconda.com/), the API Client install should still be performed using pip and not [conda](https://docs.conda.io/en/latest/).

Note: to find the location where Gro packages have been installed you can use the query:
```
pip show gro
```
## Authentication Token

1. [Retrieving a token](#retrieving-a-token)
2. [Expiring/Regenerating Tokens](#expiring-regenerating-tokens)
3. [Saving your token as an environment variable](#saving-your-token-as-an-environment-variable)

To work with the Gro API, you need an authentication token. This token needs to be sent along with every request made to the API. This is typically done by using one of the included Client classes (`Client`, `GroClient`, `BatchClient`, or `CropModel`): you provide your access token when creating the object, and then every API request made thereafter automatically includes the token. See the (MAKE LINK) sample scripts for examples.

### Retrieving a token

Note that your account needs to be activated for API access before you will be able to retrieve a token. See https://gro-intelligence.com/products/gro-api for more info regarding unlocking API access for your account.
Once you have API access enabled for your account, you may retrieve your token in any of the following ways:

1. [Using the Gro Web Application (preferred)](#option-1-using-the-web-app-recommended)
2. [Using the Gro Command Line Interface](#option-2-using-the-gro-client-command-line-interface)
3. [Using the get_access_token() Function](#option-3-using-the-get-access-token-function)

#### Option 1: Using the Web App (Recommended)

1. Log in to your Gro account at http://app.gro-intelligence.com and open your Account menu using the button on the bottom left of the Gro dashboard (see image below).
![user-profile-annotated.png](./_images/user-profile-annotated.png)

2. In the Account menu, select the API tab (see below).
![profile-tab-annotated.png](./_images/profile-tab-annotated.png)

3. Select the text of the token and copy it to your clipboard, or use the "copy to clipboard" button (see below).
![api-tab-annotated.png](./_images/api-tab-annotated.png)

#### Option 2: Using the gro_client Command Line Interface

Limitation: The Gro Command Line Interface cannot retrieve tokens for users using OAuth authentication. If this applies to you, please use the Gro web application instead.

When you install the Gro API Client via pip, the `gro_client` command line interface is automatically added to your PATH. This is a convenience tool for doing basic operations on the command line without needing to write a full Python script. One of its uses is it can retrieve your authentication token and print that token out to the console. To do so, execute the command below on your command line, substituting email@example.com for the email address associated with your Gro web application account:

```sh
gro_client --user_email=email@example.com --print_token
```

You should then be prompted for a password. Note that this password prompt does not display any user input on the command line, so it may appear as though you are not typing anything. This is intended. Simply type your password and press Enter.

If the password is accepted, your access token is printed to the console.

#### Option 3: Using the `get_access_token()` Function

Limitation: The `get_access_token()` function cannot retrieve tokens for users using OAuth authentication. If this applies to you, please use the Gro web application instead.

If you would like to programmatically retrieve your active token, you may use the `get_access_token()` function in the API Client library. See below:

```py
from api.client.lib import get_access_token
API_HOST = 'api.gro-intelligence.com'
EMAIL = 'example@example.com'
PASSWORD = 'password123'
ACCESS_TOKEN = get_access_token(API_HOST, EMAIL, PASSWORD)
```

It is generally bad practice to put login credentials directly in code as in this example, but the `get_access_token()` function may be useful for productionization purposes, making the application more robust to tokens expiring (see the next section).

### Expiring/Regenerating Tokens

There are two ways you can invalidate your current authorization token and create a new one, both of which are performed through the Gro web application:

1. Changing your password, or
2. Using the "Regenerate Token" button in the API section of your Account menu (see instructions below)
If you have your authentication token saved, performing either of these two actions will cause any applications using the old token to cease being able to contact the Gro API. You will need to follow the instructions in Section 1 to retrieve your new token and update any such applications accordingly.
To regenerate your authentication token, open the API tab in your Account menu as in Section 1.1, but instead of copying the authentication token, press the "Regenerate Token" button (see below). A prompt will appear to warn that any applications using the old token will need to be updated and to confirm your intent.

![regenerate-token.png](./_images/regenerate-token.png)

### Saving your token as an environment variable

If you don't want to enter a password or token each time, you can save the token as an environment variable. In some of the sample code, it is assumed that you have the token saved to your environment variables as `GROAPI_TOKEN`.

Please consult your OS or IDE documentation for the most accurate and up-to-date information on how to set environment variables, e.g. setting environment variables in [Windows Powershell](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-6) or [Mac OS X/Linux](https://apple.stackexchange.com/questions/106778/how-do-i-set-environment-variables-on-os-x) or [Anaconda](https://anaconda-project.readthedocs.io/en/latest/user-guide/tasks/work-with-variables.html). As a quick quide, the following steps should work:

For Windows:
1. Click on start menu and search for "environment variables." Click on "Edit the system environment variables" option.
2. In the "Advanced" tab, select the "Environment Variables..." button.
3. Under the first section called "User variables for <username>", click on the "New" button.
4. Enter the information as follows:
  Variable name: GROAPI_TOKEN
  Variable value: <insert your Gro API Token here>
5. Click OK

Your environment variable should now be saved. Whenever you run code that includes the code `os.environ['GROAPI_TOKEN']` it should automatically pull in your API Token.

For Mac:
1. Open up your terminal and navigate to your project directory
2. type `python`
3. when the python editor opens type:
`>>> import os`
`>>> os.environ['GROAPI_TOKEN'] = "YOUR TOKEN HERE"`
4. to exit type:
`>>>exit()`

Your environment variable should now be saved.
