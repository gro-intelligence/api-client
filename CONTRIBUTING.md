# Contributor's Guide

## Install Poetry

We use Poetry to manage packaging for the client library. Using Poetry for
development is encouraged. See [Poetry docs](https://python-poetry.org/docs/)
for full installation instructions.

Here's the tl;dr for OS X and Linux:

```sh
curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python -
```

## Get the client library

Clone the repo and install your cloned copy via Poetry:

```sh
git clone https://github.com/gro-intelligence/api-client.git
cd api-client
poetry install
```

Under the hood, Poetry will install a Python virtualenv and fetch the
dependencies.

## Testing

To run unit tests, you can use `poetry run`. This runs the `pytest` command
within the virtualenv that Poetry created in the previous step.

```sh
poetry run pytest
```

You can also enter the virtualenv directly in a few ways:

- `poetry shell` - this spawns a new shell with the virtualenv activated
- ```source `poetry env info -p`/bin/activate``` - the poetry command outputs
  the file path of the virtual environment, and then you source the activate
  script as usual.

Once you're in the virtualenv, you can directly run `pytest`.

## Publishing a new release

Our packages on PyPI and TestPyPI:
- https://pypi.org/project/groclient/
- https://test.pypi.org/project/groclient/

Note: Shippable is configured to automatically publish to PyPI for new releases
and TestPyPI on every build, so you normally shouldn't need to run these
commands manually. (TODO: make this so)

`poetry build` generates new source and wheel distributions in `dist/`.

To publish to PyPI, you'll need credentials. Using [PyPI API
tokens](https://pypi.org/help/#apitoken) is recommended, like so:

`poetry publish --username __token__ --password <pypi-token-value-here>`

You can also publish using the [PyPA gro-intelligence account](https://pypi.org/user/gro-intelligence/) username and password.

### Publishing to TestPyPI

Publishing to TestPyPI works the same way, though you'll also need to:

- configure the repository:
  ```sh
  poetry config repositories.testpypi https://test.pypi.org/legacy/ # only need to do this once
  poetry publish -r testpypi
  ```
- or use an environment variable:
  ```sh
  POETRY_REPOSITORIES_TESTPYPI_URL=https://test.pypi.org/legacy/ poetry publish -r testpypi
  ```
