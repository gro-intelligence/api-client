# Prevented Plant: How to Use

## For Mac & Linux

### Install the API Client

```sh
pip install git+https://github.com/gro-intelligence/api-client.git
```

### Run prevent plant

1. Download [the requirements file](./requirements.txt) to your working directory
2. Run `pip install -r requirements.txt` to automatically install the required dependencies
3. Download the notebook to your working directory
4. Run `jupyter notebook` to start the jupyter server and open the notebook in your web browser

## For Windows

Note: Use of Anaconda is recommended due to geopandas dependency. Please see <http://geopandas.org/install.html> for further details.

### Install the API client

```sh
conda install pip
pip install git+https://github.com/gro-intelligence/api-client.git
```

### Run prevent plant

1. Download [the Windows requirements file](./windows-requirements.txt) to your working directory
2. Run `conda install --file windows-requirements.txt` to automatically install the required dependencies
3. Download the notebook to your working directory
4. Make sure these lines are uncommented (see the note in the notebook regarding xgboost):

```py
from sklearn.ensemble import GradientBoostingRegressor
gbt_model = GradientBoostingRegressor()
```

5. Run `jupyter notebook` to start the jupyter server and open the notebook in your web browser
