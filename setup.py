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
    version="1.19.2",
    description="Python client library for accessing Gro Intelligence's "
                "agricultural data platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/gro-intelligence/api-client",
    packages=setuptools.find_packages(),
    python_requires=">=2.7.6, !=3.0.*, !=3.1.*, !=3.2.*, <4",
    install_requires=requirements,
    setup_requires=pytest_runner,
    test_suite='pytest',
    tests_require=test_requirements,
    entry_points={
        'console_scripts': ['gro_client=api.client.gro_client:main']
    }
)
