<p align="center"><img width=8% src="https://gro-intelligence.com/images/logo.jpg"></p>
<h1 align="center">Gro API Client</h1>

<https://www.gro-intelligence.com/products/gro-api>

Client library for accessing Gro Intelligence's agricultural data platform.

## Prerequisites

1. [MacOS and Linux](unix-setup.md)
2. [Windows](windows-setup.md)

## Install Gro API client packages

```sh
pip install git+https://github.com/gro-intelligence/api-client.git
```

Note that even if you are using [Anaconda](https://www.anaconda.com/), the API Client install should still be performed using pip and not [conda](https://docs.conda.io/en/latest/).

## Gro API authentication token

Use the Gro web application to retrieve an authentication token (detailed instructions are on the developers site [here](https://developers.gro-intelligence.com/authentication.html)).

## Examples

Navigate to [api/client/samples/](api/client/samples/) folder and try executing the provided examples.

1. Start with [quick_start.py](api/client/samples/quick_start.py). This script creates an authenticated `GroClient` object and uses the `get_data_series()` and `get_data_points()` methods to find Area Harvested series for Ukrainian Wheat from a variety of different sources and output the time series points to a CSV file. You will likely want to revisit this script as a starting point for building your own scripts.

    Note that the script assumes you have your authentication token set to a `GROAPI_TOKEN` environment variable (see [Saving your token as an environment variable](https://developers.gro-intelligence.com/authentication.html#saving-your-token-as-an-environment-variable)). If you don't wish to use environment variables, you can modify the sample script to set [`ACCESS_TOKEN`](https://github.com/gro-intelligence/api-client/blob/0d1aa2bccaa25a033e39712c62363fd89e69eea1/api/client/samples/quick_start.py#L7) in some other way.

    ```sh
    python quick_start.py
    ```

    If the API client is installed and your authentication token is set, a csv file called `gro_client_output.csv` should be created in the directory where the script was run.

2. Try out [soybeans.py](api/client/samples/crop_models/soybeans.py) to see the `CropModel` class and its `compute_crop_weighted_series()` method in action. In this example, NDVI ([Normalized difference vegetation index](https://app.gro-intelligence.com/dictionary/items/321)) for provinces in Brazil is weighted against each province's historical soybean production to put the latest NDVI values into context. This information is put into a pandas dataframe, the description of which is printed to the console.

    ```sh
    python crop_models/soybeans.py
    ```

3. See [brazil_soybeans.ipynb](https://github.com/gro-intelligence/api-client/blob/development/api/client/samples/crop_models/brazil_soybeans.ipynb) for a longer, more detailed demonstration of many of the API's capabilities in the form of a Jupyter notebook.

4. You can also use the included `gro_client` tool as a quick way to request a single data series right on the command line. Try the following:

    ```sh
    gro_client --metric="Production Quantity mass" --item="Corn" --region="United States" --user_email="email@example.com"
    ```

    The `gro_client` command line interface does a keyword search for the inputs and finds a random matching data series. It displays the data series it picked and the data points to the console. This tool is useful for simple queries, but anything more complex should be done using the provided Python packages.

Further documentation can be found on the Gro Developers site at <developers.gro-intelligence.com>.
