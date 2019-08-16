import setuptools
import sys

needs_pytest = {'pytest', 'test', 'ptr'}.intersection(sys.argv)
pytest_runner = ['pytest-runner'] if needs_pytest else []

with open("README.md", "r") as readme_file:
    long_description = readme_file.read()

with open("requirements.txt", "r") as requirements_file:
    requirements = requirements_file.read()

with open("test-requirements.txt", "r") as test_requirements_file:
    test_requirements = test_requirements_file.read()

setuptools.setup(
    name="gro",
    version="1.19.3",
    description="Python client library for accessing Gro Intelligence's "
                "agricultural data platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gro-intelligence/api-client",
    packages=setuptools.find_packages(),
    python_requires=">=2.7.12, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*, <4",
    install_requires=requirements,
    extras_require={
        'docs': [
            # sphinx 1.6+ is incompatible with sphinxcontrib-versioning as of
            # 2019-08-16 (version 2.2.1). Project is transferring ownership currently.
            # TODO: revisit later to see if it has been revived.
            # https://github.com/sphinx-contrib/sphinxcontrib-versioning/issues/59
            'sphinx==1.5.6',
            'recommonmark',
            'sphinx_rtd_theme',
            'sphinxcontrib-versioning'
        ]
    },
    setup_requires=pytest_runner,
    test_suite='pytest',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': ['gro_client=api.client.gro_client:main']
    }
)
