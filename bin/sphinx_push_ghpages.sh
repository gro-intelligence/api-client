#!/bin/bash

# This script replicates basic `sphinx-versioning push` functionality for
# sphinx-multiversion. It should be run from the base of the git repo.
# It's largely based on sphinxcontrib-versioning's code:
# https://github.com/sphinx-contrib/sphinxcontrib-versioning/blob/920edec0ac764081b583a2ecf4e6952762b9dbf2/sphinxcontrib/versioning/__main__.py#L332

set -e -u -o pipefail

# Branch to push the generated docs to.
PAGES_BRANCH=gh-pages
# Which branch to store at the root of the docs. Analogous to scv_root_ref:
# https://sphinxcontrib-versioning.readthedocs.io/en/latest/settings.html#cmdoption-r
ROOT_REF=development
# Files to keep in the repo. Analogous to scv_grm_exclude:
# https://sphinxcontrib-versioning.readthedocs.io/en/latest/settings.html#cmdoption-e
KEEP_FILES=(.nojekyll CNAME README.md shippable.yml)

# get origin repo. assumes fetch and pull locations are the same.
REPO=$(git remote -v | grep origin | awk 'NR==1 { print $2 }')
TMPDIR=$(mktemp -d ./tmp-sphinx.XXX)


## prepare helper repo

# clone into temp dir
echo -e "\n-> cloning $REPO to temp dir $TMPDIR..."
cd "$TMPDIR"
git clone "$REPO" --quiet --depth=1 --branch="${PAGES_BRANCH}" .
# remove old files
git rm -rf --quiet .
# restore some files we want to keep. note: using bash array syntax.
git reset --quiet HEAD -- "${KEEP_FILES[@]}"
git checkout -- "${KEEP_FILES[@]}"


## build docs

echo -e "\n-> building docs..."
# 'sphinx-multiversion ../docs .' fails, so we just cd back out for this step.
cd ..
sphinx-multiversion docs "$TMPDIR"
cd "$TMPDIR"

# With sphinxcontrib-versioning, we would generate a separate directory of docs
# for each version tag and branch, but also have the 'development' branch's
# docs at the top level.  sphinx-multiversion only generates the separate
# directories. To avoid breaking links, we copy the the root ref docs (i.e.,
# the development branch docs) to the parent directory containing all docs.
echo -e "\n-> copying root ref ($ROOT_REF) to docs root..."
cp -R "${ROOT_REF}/." .

echo -e "\n-> checking for changes..."
git add .
# ignore trivial changes (.doctrees and .buildinfo files are always modified
# when rebuilding the docs). Notes:
# - '|| true' is needed because when grep fails to match something, it returns
#   a non-zero exit code, which causes the script to fail due to the 'pipefail'
#   setting.
# - this logic differs from sphinxcontrib-versioning slightly. SCV ignores
#   searchindex.js but not .buildinfo. I didn't notice searchindex.js being
#   regenerated unnecessarily, but did see that happening with .buildinfo files.
CHANGED=$(git diff HEAD --no-ext-diff --name-status | grep -v '^M.*\.doctrees/' | grep -v '^M.*\.buildinfo$' || true)
if [ -z "$CHANGED" ]; then
  echo -e "\n-> no changes, done!"
  exit 0
else
  echo -e "\n-> found changed files:"
  echo "$CHANGED"
fi

echo -e "\n-> committing change..."
git commit -m "sphinx_push_ghpages.sh: autocommit $(date '+%Y-%m-%d %H:%M:%S')"

echo -e "\n-> pushing update..."
git push origin "$PAGES_BRANCH"

echo -e "\n-> done!"
