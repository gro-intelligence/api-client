Prerequisite Software Package Installation
##########################################

The following links are provided for guidance on installing the prerequisite software.
 
MacOS and Linux
===============

1. git `Installation instructions <https://git-scm.com/book/en/v2/Getting-Started-Installing-Git>`_
2. python version 3.5 or above from `<https://www.python.org>`_. Support for Python 2.7.13 or above is also maintained, but with its `End of Life <https://mail.python.org/pipermail/python-dev/2018-March/152348.html>`_, Python 3 is recommended.
3. MacOS comes with an old version of python 2 which is incompatible with the Gro API client. See the following link for `installing Python 3 on MacOS <https://docs.python-guide.org/starting/install3/osx/>`_ without disrupting the base install

Windows
=======

The Gro API Client package is supported both with or without Anaconda. However, some popular data science packages, including some used in the sample scripts provided, are only available on Windows via `conda <https://docs.conda.io/en/latest/>`_. For that reason, instructions are provided for both. You should select the distribution that fits your requirements.

Anaconda
--------
1. Download Anaconda with Python 3.5 or above from `anaconda.com <https://www.anaconda.com/distribution/>`_ Support for Python 2.7.13 or above is also maintained, but with `its End of Life <https://mail.python.org/pipermail/python-dev/2018-March/152348.html>`_, it is recommended you start with Python 3.
2. Install Git from `git-scm.com <https://git-scm.com/download/win>`_. Proceed with the default options.
3. See `additional information <./anaconda-additional-information>`_ related to Anaconda if Anaconda is not installed in the default directory (C:\Users\<your-username>) or if your environment uses a proxy or firewall in connections to the internet.

Non-Anaconda 
------------
#. Powershell (should come default with Windows)
#. Download Python version 3.5 or above from `python.org <https://www.python.org/downloads/windows/>`_. Support for Python 2.7.13 or above is also maintained, but with `its End of Life <https://mail.python.org/pipermail/python-dev/2018-March/152348.html>`_, it is recommended you start with Python 3.
#. Install both Python and pip to PATH either in the installer (enable component during the installation) or manually. The easiest way to do this is to make sure the below is checked during installation:

   .. image:: ../_images/python3-path.PNG
    :align: center
    :alt: Add python to path installer
  
#. Install Git from `git-scm.com <https://git-scm.com/download/win>`_. Proceed with the default options.
