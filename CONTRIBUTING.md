# Contributor's Guide

## Install the client library in editable mode

First, make sure you do not have the client library installed already:

```sh
$ pip uninstall groclient
```

Then, clone the repo and install your cloned copy in editable mode (`-e`)

```sh
$ git clone https://github.com/gro-intelligence/api-client.git
$ pip install -e ./api-client
```

This will allow you to make modifications to the client library and test them, as well as checkout different branches and immediately see the changes without needing to reinstall each time.

## Testing

To run unit tests, install the testing requirements and then execute with pytest:

```sh
$ pip install ./api-client[test]
$ pytest --cov
```

## Packaging

```sh
$ pip install '.[package]'
$ rm -rf dist && python setup.py sdist bdist_wheel --universal
```

Upload to PyPI (upload to TestPyPI with `-r testpypi`):

```sh
$ twine upload -u __token__ -p <pypi-token> dist/*
```

You can install from TestPyPI for testing purposes (probably in separate new
virtual environment) like so:

```sh
$ pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple groclient==<some-specific-version>
```
