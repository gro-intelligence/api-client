# Contributor's Guide

## Install the client library in editable mode

First, make sure you do not have the client library installed already:

```sh
$ pip uninstall gro
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