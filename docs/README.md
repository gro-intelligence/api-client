# Documentation

## Add/Modify Content

Create a \*.md file or \*.rst file in this /docs directory, and they will be
added as new pages automatically.

The API reference page, [api.rst](api.rst) uses
[sphinx.ext.autodoc](http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html)
to automatically pull docstrings from `GroClient` and `CropModel`, so any
function docstrings added or modified in those modules will be updated in the
documentation. All other pages are manually written.

## Build docs locally

- Install Poetry (see `CONTRIBUTING.md`).
- `poetry install -E docs` to install extra dependencies.
- `rm -r docs/_build/html && poetry run sphinx-build -W --keep-going docs
  docs/_build/html` to build the docs for your current branch.

This should generate html output in `api-client/docs/_build/html` that you can
open up and view in a web browser.

## Automatic builds

Every time continuous integration runs it should be re-building the
documentation for any currently-open branches and pushing the result to the
`gh-pages` branch. If you edit any documentation pages or docstrings, it should
be a part of the Pull Request review process that you navigate to your feature
branch's built documentation and verify that the changes are as intended.

Note that branches aren't listed in the version-selector widget (since we don't
want to show it to external users), but you can navigate directly to it:
`https://developers.gro-intelligence.com/<YOUR-BRANCH-NAME-HERE>/index.html`

If anything in continuous integration fails, the documentation building step is
skipped.
