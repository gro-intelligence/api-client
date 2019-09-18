# Quickstart Examples

Now that you have installed the basic requirements, you can start pulling data. Try out the examples below, or navigate to the [api/client/samples/](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples) folder for more options.

## Quickstart.py

[quick_start.py](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/quick_start.py) is a simple script that creates an authenticated `GroClient` object and uses the `get_data_series()` and `get_data_points()` methods to find Area Harvested series for Ukrainian Wheat from a variety of different sources, and outputs the time series points to a CSV file. You will likely want to revisit this script as a starting point for building your own scripts.

Note that the script assumes you have your authentication token set to a `GROAPI_TOKEN` environment variable ([see Saving your token as an environment variable](.docs/authentication.md). If you don't wish to use environment variables, you can modify the sample script to set `ACCESS_TOKEN` in some other way.

```sh
$ python quick_start.py
```

If the API client is installed and your authentication token is set, a CSV file called `gro_client_output.csv` should be created in the directory where the script was run.

## Soybeans.py

Try out [soybeans.py](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/crop_models/soybeans.py) to see the `CropModel` class and its `compute_crop_weighted_series()` method in action. In this example, NDVI ([normalized difference vegetation index](https://app.gro-intelligence.com/dictionary/items/321)) for provinces in Brazil is weighted against each province's historical soybean production to put the latest NDVI values into context. This information is put into a pandas dataframe, the description of which is printed to the console.

```sh
python crop_models/soybeans.py
```

## Brazil Soybeans

See the [Brazil Soybeans](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/crop_models) example in the crop models folder for a longer, more detailed demonstration of many of the API's capabilities in the form of a Jupyter notebook.

## gro_client tool

You can also use the included gro_client tool as a quick way to request a single data series right on the command line. Try the following:

```sh
gro_client --metric="Production Quantity mass" --item="Corn" --region="United States" --user_email="email@example.com"
```

The gro_client command line interface does a keyword search for the inputs and finds a random matching data series. It displays the data series it picked in the command line and writes the data points out to a file in the current directory called gro_client_output.csv. This tool is useful for simple queries, but anything more complex should be done using the Python packages.