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

Clone the repo:

```sh
git clone https://github.com/gro-intelligence/api-client.git
cd api-client
```

Install dependencies as well as a local editable copy of the library:

```sh
poetry install
```

Under the hood, Poetry will install a Python virtualenv and fetch the
dependencies.

- `poetry env info` to see where the virtualenv is.
- `poetry env remove <env-name>` to delete the environment. (You can also just
  specify the Python version, eg: `poetry env remove 3.8`)

## Testing

To run unit tests:

```sh
poetry run pytest
```

`poetry run` will run the `pytest` command within the virtualenv that Poetry
created previously.

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

**Notes:**

- Shippable is configured to automatically publish to PyPI for new releases and
  TestPyPI whenever new PRs are merged to the `development` branch, so you
  normally shouldn't need to run these commands manually.
- We use
  [poetry-dynamic-versioning](https://github.com/mtkennerly/poetry-dynamic-versioning)
  to automatically set the package version based on Git tags. If building
  locally, you'll need to `pip install poetry-dynamic-versioning` to get
  versioning to work. Hopefully this will become easier once Poetry has
  a plugin system. In the meantime, we rely on Shippable to take care of this
  for us.

To build new source and wheel distributions in `dist/`:

```sh
poetry build
```

To publish to PyPI, you'll need credentials. Using [PyPI API
tokens](https://pypi.org/help/#apitoken) is recommended, like so:

```sh
poetry publish --username __token__ --password <pypi-token-value-here>
```

You can also publish with the username and password for the [gro-intelligence
account on PyPA](https://pypi.org/user/gro-intelligence/).

### Publishing to TestPyPI

You'll need to first configure the repository:

- configure the repository (only need to do this once): `poetry config
  repositories.testpypi https://test.pypi.org/legacy/`
- or, use an environment variable: `export
  POETRY_REPOSITORIES_TESTPYPI_URL=https://test.pypi.org/legacy/`

Then add `-r testpypi` to the publish command:

```sh
poetry publish -r testpypi --username __token__ --password <pypi-token-value-here>
```
