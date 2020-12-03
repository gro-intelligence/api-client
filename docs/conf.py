# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# http://www.sphinx-doc.org/en/master/config

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys
sys.path.insert(0, os.path.abspath('..'))


# -- Project information -----------------------------------------------------

project = 'Gro API Client'
html_logo = '_images/logo.jpg'
copyright = '2020, Gro Intelligence'
author = 'Gro Intelligence'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.coverage',
    'sphinx.ext.doctest',
    'sphinx.ext.extlinks',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'recommonmark',
    'sphinx_multiversion',
    'nbsphinx'
]

source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', 'README.md']

# -- Options for HTML output -------------------------------------------------

html_theme = 'sphinx_rtd_theme'

html_theme_options = {
    'collapse_navigation': False,
    'sticky_navigation': True,
    'navigation_depth': 1,
    'includehidden': False,
    'titles_only': False,
    'prev_next_buttons_location': 'both',
    'style_external_links': True,
    'display_version': True,
    'logo_only': True
}

html_style = 'css/custom-theme.css'

# https://www.sphinx-doc.org/en/master/usage/extensions/extlinks.html
extlinks = {
    'sample': (
        'https://github.com/gro-intelligence/api-client/tree/development/api/client/samples/%s', ''
    )
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static', '_images']

master_doc = 'index'


# -- sphinx-multiversion options ---------------------------------------------

# v1.40.6 (from 2019-12-19) is the first version with finalized docs style.
# so, we ignore all other releases that preceded that.
smv_tag_whitelist = r'^v(?!1\.40\.[012345]).+$'

# By default, sphinx-multiversion doesn't build remote branches. We want to
# build all branches, so we sent the pattern to something that matches
# everything.
smv_remote_whitelist = r'.'

# Exclude the 'HEAD' ref from being built. Due to building remote refs with
# smv_remote_whitelist, SMV will build the remotes/origin/HEAD ref. This is
# equivalent to the 'development' branch, so no need to build it again.
smv_branch_whitelist = r'^(?!HEAD).*$'

# Note: see bin/sphinx_push_ghpages.sh for how we push new documentation to
# GitHub Pages. Some options related to pushing docs changes that used to be
# set here for sphinxcontrib-versioning are now configured in the script, since
# sphinx-multiversion doesn't have built-in support for pushing changes.
