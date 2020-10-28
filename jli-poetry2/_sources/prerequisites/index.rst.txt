#############
Prerequisites
#############

.. contents:: Table of Contents
  :local:

User Skills
===========

The user(s) should be:

1. Familiar with command line syntax
    a. MacOS: Terminal
    b. Windows: Command Prompt / Powershell
    c. Linux: Command Line
2. Experienced in Python
3. Experienced with Jupyter notebooks (preferred)

Software Packages
=================

The following software packages must be installed in the environment(s) that will be used to access the Gro API prior to trying to install the Gro API client package. See environment-specific instructions for installing `prerequisite software packages <./software-packages-prereqs>`_.

1. Git 
2. Python
    * Python version 3.5 or above is recommended. Support for Python 2.7.13 or above is also maintained, but with its `End of Life <https://mail.python.org/pipermail/python-dev/2018-March/152348.html>`_ now passed, Python 3 is recommended for any new installations.
3. Pip (should be installed as part of the python installation)

Network communication
=====================

The environment must have access to the following resources in order to download and install the Gro API client:

* github
    * github.com (port 443 - https) or (port 80 - http)
    * github.com (port 9418)
    * github.com (port 22)
* python.org
    * pypi.python.org (port 443 - https) or (port 80 - http)
    * pypi.python.org (port 3128)
* pythonhosted.org
    * files.pythonhosted.org (port 443 - https) or (port 80 - http)
    * files.pythonhosted.org (port 3128)
* api.gro-intelligence.com
    * API hosts (port 443 - https)
    * See `additional information <./gro-api-corporate-proxy>`_ if Gro API will be installed in an environment that uses a proxy to communicate with the internet
