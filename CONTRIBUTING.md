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

- Shippable is configured to automatically publish to PyPI whenever new
  releases are tagged on GitHub (and to TestPyPI whenever new PRs are merged
  to `development`), so you normally shouldn't need to run these commands manually.
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

### Conda package details

`groclient` is available for Conda/Anaconda users via the [Conda
Forge](https://conda-forge.org/) channel. The developer documentation
includes [installation instructions for Conda
users](https://developers.gro-intelligence.com/installation.html).

The groclient conda package is configured via the
[conda-forge/groclient-feedstock](https://github.com/conda-forge/groclient-feedstock)
GitHub repo, which is maintained by Gro team members. (See [conda-forge
docs](https://conda-forge.org/docs/maintainer/updating_pkgs.html#updating-the-maintainer-list)
and [PR#4](https://github.com/conda-forge/groclient-feedstock/pull/4) for how
to add more people to be maintainers.)

Our feedstock repo is automatically maintained for the most part. We've
[configured](https://github.com/conda-forge/groclient-feedstock/pull/3) the
conda forge bot to automatically publish new packages to Conda when there are
new version released to PyPI.

Other relevant resources:

- Background on Conda: https://jakevdp.github.io/blog/2016/08/25/conda-myths-and-misconceptions/
- The groclient package on Conda: https://anaconda.org/conda-forge/groclient
- Added groclient to conda-forge here: https://github.com/conda-forge/staged-recipes/pull/13255
  - The conda-forge "recipe" was [auto-generated using
    grayskull](https://github.com/conda-forge/staged-recipes#grayskull---recipe-generator-for-python-packages-on-pypi)
    based on our PyPI package.
  - Our conda-forge "feedstock" repo: https://github.com/conda-forge/groclient-feedstock
