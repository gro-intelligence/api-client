# python setup.py sdist bdist_wheel

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name = "gro",
    version = "1.12.0",
    description = "A client library for accessing Gro Intelligence's agriculture data platform",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/gro-intelligence/api-client",
    packages = [ 'api', 'api.client' ],
    py_modules = [ 'api.client.lib' ],
    python_requires = ">=2.7.6",
    install_requires = [
      'unicodecsv',
      'numpy',
      'pandas',
      'python-dateutil',
      'pytz',
      'certifi',
      'chardet',
      'requests',
      'urllib3',
      'future',
    ],
    entry_points={
      'console_scripts': ['gro=api.client.gro_client:main']
    }
)
