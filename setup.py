# TODO(jli): after moving to poetry and migrating users to using the pip
# package, i think we can remove setup.py and all requirements.txt files.

import setuptools
import sys

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

with open("requirements.txt", "r") as requirements_file:
    requirements = requirements_file.read()

with open("requirements-test.txt", "r") as test_requirements_file:
    test_requirements = test_requirements_file.read()

with open("requirements-docs.txt", "r") as docs_requirements_file:
    docs_requirements = docs_requirements_file.read()

setuptools.setup(
    name="groclient",
    description="Python client library for accessing Gro Intelligence's "
                "agricultural data platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gro-intelligence/api-client",
    packages=setuptools.find_packages(),
    python_requires=">=3.6, <4",
    install_requires=requirements,
    extras_require={
        'docs': docs_requirements,
        'test': test_requirements
    },
    # root must be current directory
    # otherwise, use_scm_version = {"root": path, "relative_to": __file__}
    use_scm_version=True,
    setup_requires=pytest_runner + ['setuptools_scm'],
    test_suite='pytest',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': ['gro_client=groclient.__main__:main']
    }
)
