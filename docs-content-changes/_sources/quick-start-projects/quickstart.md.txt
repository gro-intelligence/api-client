# Quickstart.py

[quick_start.py](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/quick_start.py) is a simple script that creates an authenticated `GroClient` object and uses the `get_data_series()` and `get_data_points()` methods to find Area Harvested series for Ukrainian Wheat from a variety of different sources, and outputs the time series points to a CSV file. You will likely want to revisit this script as a starting point for building your own scripts.

Note that the script assumes you have your authentication token set to a `GROAPI_TOKEN` environment variable ([see Saving your token as an environment variable](./authentication#saving-your-token-as-an-environment-variable). If you don't wish to use environment variables, you can modify the sample script to set `ACCESS_TOKEN` in some other way.

```sh
$ python quick_start.py
```

If the API client is installed and your authentication token is set, a CSV file called `gro_client_output.csv` should be created in the directory where the script was run.
