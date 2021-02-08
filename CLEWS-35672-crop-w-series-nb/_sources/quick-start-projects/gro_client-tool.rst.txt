################
gro_client tool
################

You can also use the included gro_client tool as a quick way to request a single data series right on the command line. Try the following:
::

  gro_client --metric="Production Quantity mass" --item="Corn" --region="United States" --user_email="email@example.com"


The gro_client command line interface does a keyword search for the inputs and finds a random matching data series. It displays the data series it picked in the command line and writes the data points out to a file in the current directory called gro_client_output.csv. This tool is useful for simple queries, but anything more complex should be done using the Python packages.