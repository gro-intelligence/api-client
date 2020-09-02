# Documentation

## Add/Modify Content

Create a \*.md file or \*.rst file in this /docs directory, and they will be added as new pages automatically.

The API reference page, [api.rst](api.rst) uses [sphinx.ext.autodoc](http://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html) to automatically pull docstrings from `GroClient` and `CropModel`, so any function docstrings added or modified in those modules will be updated in the documentation. All other pages are manually written.

## Build docs locally

From the project root (`api-client/`) run the below command:

```sh
sphinx-versioning build docs docs/_build/html
```

It should generate html in `api-client/docs/_build/html` that you can open up and view in a web browser.

## Automatic builds

Every time continuous integration runs it should be re-building the documentation for any currently-open branches and pushing the result to the `gh-pages` branch. If you edit any documentation pages or docstrings, it should be a part of the Pull Request review process that you navigate to your feature branch's built documentation and verify that the changes are as intended.

If anything in continuous integration fails, the documentation building step is skipped.
