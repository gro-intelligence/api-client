###################
Get Started in 120 Seconds
###################

If you have a Google account, or if you already have `Jupyter Notebook <https://jupyter.readthedocs.io/en/latest/install.html>`_ and python installed, and a Gro API token, you can start pulling Gro data via our API client within 120 seconds.

Step 1: Get your API token
--------------------------

1. Login to your Gro web app account at https://app.gro-intelligence.com
2. Open the Account button in the bottom left corner of the app.

  .. image:: ../_images/account-button.PNG
    :align: center
    :alt: Account button

3. Navigate to the API tab.

  .. image:: ../_images/account-api-section.PNG
    :align: center
    :alt: Account api section

4. Copy your token.

Step 2: Run the code in a notebook
----------------------------------

1. Navigate to `Google Colab <https://colab.research.google.com/>`_, or launch Jupyter Notebook from your command line with the command :code:`jupyter notebook`.
2. Copy the below code and paste it into the first cell.

  ::

    !pip install git+https://github.com/gro-intelligence/api-client.git

  Then click the "Run Cell" button to the left of the cell.
  In Colab, it will look like this:

  .. image:: ../_images/colab-run-button.PNG
    :align: center
    :alt: Colab run button

  In Jupyter Notebook, it looks like this:

  .. image:: ../_images/jupyter-run-button.PNG
    :align: center
    :alt: Jupyter run button

3. Add another cell with the "+ Code" button, then copy the below code and paste it into the second cell.

  ::

    from groclient import GroClient
    client = GroClient('api.gro-intelligence.com', '<YOUR_TOKEN>')


4. Replace the text <YOUR_TOKEN> with the token you copied from step one. Then click the "Run Cell" button to the left of the cell.

5. Add one more cell with the "+ Code" button, then copy the below code and paste it into the third cell.

  ::

    # Rice, milled - Area Harvested (area) - Kenya (USDA PS&D)
    client.get_data_points(**{
      'metric_id': 570001,
      'item_id': 392,
      'region_id': 1107,
      'source_id': 14,
      'frequency_id': 9
    })

6. Click the "Run Cell" button to the left of the cell, and that's it! You should now see the data in the response.

Step 3: Bonus Round
-------------------

1. Go to the Gro `web app <https://app.gro-intelligence.com>`_ and choose a chart that you like.

2. Click the dropdown arrow in the top right of the chart.

  .. image:: ../_images/chart-dropdown.PNG
    :align: center
    :alt: Chart dropdown

3. Click Export, and then click API Client Code Snippets.

  .. image:: ../_images/export-code-snippet.PNG
    :align: center
    :alt: Export code snippet

4. Copy to code from the pop up window.

  .. image:: ../_images/code-snippet-window.PNG
    :align: center
    :alt: Code snippet window

5. Add another cell with the "+ Code" button, then paste the code you just copied.

6. Click the "Run Cell" button to the left of the call. Congrats! You've just discovered data in the web app and then pulled it via the API client.

  .. image:: ../_images/snippet-response.PNG
    :align: center
    :alt: Snippet response
      ![snippet-response]
