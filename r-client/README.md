# Gro API Client R Usage Example

This is a proof of concept use of the Gro API Python client https://github.com/gro-intelligence/api-client, imported and used in R via the `reticulate` R library. No special formatting or configuration needs to be done to the API client itself as plain Python functions interop with R inputs and outputs.

What this Vagrantfile does is it creates an Ubunutu 16.04 virtual machine, installs Python and R dependencies, and runs an R script emulating the quickstart example from https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/quick_start.py outputing an R dataframe at the end.

This is implemented as a Vagrantfile to demonstrate exactly what dependencies are required in this specific test environment. This example is in no way saying you must or should use Vagrant if intending to use the Gro API in R yourself. It is also important to note that because R is not an officially supported language for using the Gro API, it may take extra configuration on the user's part, and not all features are tested.

##Pre-requisites for running this example

* vagrant
* virtualbox

##Preparation

In [src/testscript.R](src/testscript.R) replace the token string with your own token. See the README in the main repo here https://github.com/gro-intelligence/api-client for details on how to retrieve a token.

##Run

```sh
$ vagrant up
```

##To use this VM for testing your own R scripts

Modify [src/testscript.R](src/testscript.R) or create a copy of it, and replace the add_single_data_series and get_df lines with your own logic. Then,

```sh
$ vagrant ssh
  password: vagrant
$ Rscript /vagrant/<your-script>
```

to run your own version of the script. Note it will create a new virtual environment and reinstall the Gro API client each time, so it does take a little while to run.

##Destroy

```sh
$ vagrant destroy default -f
```

##Documentation

* https://github.com/gro-intelligence/api-client/wiki
* https://github.com/rstudio/reticulate
* https://rstudio.github.io/reticulate/articles/calling_python.html
