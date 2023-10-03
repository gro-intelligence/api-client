##############
Authentication
##############

.. contents:: Table of Contents
  :local:

To work with the Gro API, you need an authentication token. This token needs to be sent along with every request made to the API. This is typically done by using one of the included Client classes (:code:`GroClient` or :code:`CropModel`): you provide your access token when creating the object, and then every API request made thereafter automatically includes the token.

Retrieving a token
==================

Note that your account needs to be activated for API access before you will be able to retrieve a token. See https://gro-intelligence.com/products/gro-api for more info regarding unlocking API access for your account.
Once you have API access enabled for your account, you may retrieve your token in the following way:


  1. Log in to your Gro account at https://app.gro-intelligence.com and open your Account menu using the button on the bottom left of the Gro dashboard (see image below).
  
  .. image:: ./_images/user-profile-annotated.png
    :align: center
    :alt: Profile Menu

  2. In the Account menu, select the API tab (see below).
  
  .. image:: ./_images/profile-tab-annotated.png
    :align: center
    :alt: Profile

  3. Select the text of the token and copy it to your clipboard, or use the "Copy to clipboard" button (see below).
  
  .. image:: ./_images/api-tab-annotated.png
    :align: center
    :alt: API tab



Expiring/Regenerating Tokens
============================

There are two ways you can invalidate your current authorization token and create a new one, both of which are performed through the Gro web application:

1. Changing your password, or
2. Using the "Regenerate Token" button in the API section of your Account menu (see instructions below)

If you have your authentication token saved, performing either of these two actions will cause any applications using the old token to cease being able to contact the Gro API. You will need to follow the instructions in Section 1 to retrieve your new token and update any such applications accordingly.

To regenerate your authentication token, open the API tab in your Account menu as in `Option 1: Using the Web App (Recommended)`_, but instead of copying the authentication token, press the "Regenerate Token" button (see below). A prompt will appear to warn that any applications using the old token will need to be updated and to confirm your intent.

.. image:: ./_images/regenerate-token.png
    :align: center
    :alt: Regenerate token


Saving your token as an environment variable
============================================

If you don't want to enter a password or token each time, you can save the token as an environment variable. In some of the sample code, it is assumed that you have the token saved to your environment variables as :code:`GROAPI_TOKEN`.

Please consult your OS or IDE documentation for the most accurate and up-to-date information on how to set environment variables. The links below should provide some guidance on how to do this for your preferred environment.

For Windows 10
--------------
For Anaconda, please refer to `Anaconda's Documentation <https://docs.conda.io/projects/conda/en/latest/user-guide/tasks/manage-environments.html#setting-environment-variables>`_.

If you are using Windows Powershell, you can refer to `Windows' Documentation <https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_environment_variables?view=powershell-6>`_.


For Mac and Linux
-----------------
For MacOS, you can find official instructions for setting environment variables on `Apple's website <https://support.apple.com/guide/terminal/use-environment-variables-apd382cc5fa-4f58-4449-b20a-41c53c006f8f/mac>`_ . The same instructions also apply to Linux. Note that with MacOS Catalina, Apple changed its default shell from bash to zsh, which affects where you set the variable. As a quick overview see the steps below:

1. Open your terminal and type :code:`echo $SHELL` to determine what shell you are using.
2. If the result is :code:`/bin/bash` then run :code:`open ~/.bashrc`. If the result is :code:`/bin/zsh`, then run :code:`open ~/.zshrc`. If you are using another shell, please reference your shell-specific documentation.
3. In that file, add the following line: :code:`export GROAPI_TOKEN='YOUR TOKEN HERE'`
4. Save the file and close any shells you have open. The environment variable should be available next time you open a shell.
