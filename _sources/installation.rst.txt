############
Installation
############

.. contents:: Table of Contents
  :local:


Install with pip
================

Install the latest package from `PyPI <https://pypi.org/>`_:

::

  pip install groclient

Notes:

* Even if you are using `Anaconda <https://www.anaconda.com/>`_, the API Client install should still be performed using pip and *not* `conda <https://docs.conda.io/en/latest/>`_.
* If you're unable to access PyPI, you can install the latest code from Github: :code:`pip install git+https://github.com/gro-intelligence/api-client.git`


Inspect the package
===================

To find the location on your filesystem where the Gro package has been installed and to see the version you have installed you can use the query:

::

  pip show groclient


Stay updated
============

To ensure that you have the latest client version with newest features, you can use the following command:

::

  pip install --upgrade groclient
