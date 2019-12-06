# Authentication

To work with the Gro API, you need an authentication token. This token needs to be sent along with every request made to the API. This is typically done by using one of the included Client classes (`Client`, `GroClient`, `BatchClient`, or `CropModel`): you provide your access token when creating the object, and then every API request made thereafter automatically includes the token.

## Retrieving a token

Note that your account needs to be activated for API access before you will be able to retrieve a token. See <https://gro-intelligence.com/products/gro-api> for more info regarding unlocking API access for your account.
Once you have API access enabled for your account, you may retrieve your token in any of the following ways:

1. [Using the Gro Web Application (preferred)](#option-1-using-the-web-app-recommended)
2. [Using the Gro Command Line Interface](#option-2-using-the-gro-client-command-line-interface)
3. [Using the get_access_token() Function](#option-3-using-the-get-access-token-function)

### Option 1: Using the Web App (Recommended)

1. Log in to your Gro account at <https://app.gro-intelligence.com> and open your Account menu using the button on the bottom left of the Gro dashboard (see image below).
    ![user-profile-annotated.png](./_images/user-profile-annotated.png)
2. In the Account menu, select the API tab (see below).
    ![profile-tab-annotated.png](./_images/profile-tab-annotated.png)
3. Select the text of the token and copy it to your clipboard, or use the "Copy to clipboard" button (see below).
    ![api-tab-annotated.png](./_images/api-tab-annotated.png)

### Option 2: Using the gro_client Command Line Interface

Limitation: The Gro Command Line Interface cannot retrieve tokens for users using OAuth authentication. If this applies to you, please use the Gro web application instead.

When you install the Gro API Client via pip, the `gro_client` command line interface is automatically added to your PATH. This is a convenience tool for doing basic operations on the command line without needing to write a full Python script. One of its uses is it can retrieve your authentication token and print that token out to the console. To do so, execute the command below on your command line, substituting email@example.com for the email address associated with your Gro web application account:

```sh
gro_client --user_email="email@example.com" --print_token
```

You should then be prompted for a password. Note that this password prompt does not display any user input on the command line, so it may appear as though you are not typing anything. This is intended. Simply type your password and press Enter.

If the password is accepted, your access token is printed to the console.

### Option 3: Using the `get_access_token()` Function

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

## Expiring/Regenerating Tokens

There are two ways you can invalidate your current authorization token and create a new one, both of which are performed through the Gro web application:

1. Changing your password, or
2. Using the "Regenerate Token" button in the API section of your Account menu (see instructions below)

If you have your authentication token saved, performing either of these two actions will cause any applications using the old token to cease being able to contact the Gro API. You will need to follow the instructions in Section 1 to retrieve your new token and update any such applications accordingly.

To regenerate your authentication token, open the API tab in your Account menu as in [Retrieving a token, Option 1: Using the Web App](#option-1-using-the-web-app-recommended), but instead of copying the authentication token, press the "Regenerate Token" button (see below). A prompt will appear to warn that any applications using the old token will need to be updated and to confirm your intent.

![regenerate-token.png](./_images/regenerate-token.png)

## Saving your token as an environment variable

If you don't want to enter a password or token each time, you can save the token as an environment variable. In some of the sample code, it is assumed that you have the token saved to your environment variables as `GROAPI_TOKEN`.

Please consult your OS or IDE documentation for the most accurate and up-to-date information on how to set environment variables. The links below should provide some guidance on how to do this for your preferred environment.

### For Windows 10

For Anaconda, please refer to [Anaconda's Documentation](https://anaconda-project.readthedocs.io/en/latest/user-guide/tasks/work-with-variables.html).

If you are using Windows Powershell, you can refer to [Windows' Documentation](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-6).

### For Mac

You can find official instructions for setting environment variables from [Apple's Stack Exchange](https://apple.stackexchange.com/questions/106778/how-do-i-set-environment-variables-on-os-x), or as quick guide you can follow these steps:

1. Open your terminal and type `echo $SHELL` to determine what shell you are using.
2. If the result is `/bin/bash` then run `open ~/.bashrc`. If the result is `/bin/zsh`, then run `open ~/.zshrc`. If you are using another shell, please reference your shell-specific documentation.
3. In that file, add the following line: `export GROAPI_TOKEN="YOUR TOKEN HERE"`
4. Save the file and close any shells you have open. The environment variable should be available next time you open a shell.
