:orphan:

..
	:orphan: is to suppress the warning "document isn't included in any toctree".
	This page is linked to from prerequisites/index.rst.

Anaconda Additional Information
###############################

#. If your username includes spaces, as is common on Windows systems, you are not allowed to install Anaconda in the default path (C:\Users\<your-username>\Anaconda3\)

	a. See this `Anaconda link <https://docs.anaconda.com/anaconda/user-guide/faq/#distribution-faq-windows-folder>`_ for additional information.

#. If you install Anaconda outside of the default path, then you will need to update the config for the jupyter notebook default directory as outlined below:

	a. Go to the default path (C:\Users/\<your-username>)
	b. Open the '.jupyter' folder (note the period '.' before the word 'jupyter')
	c. Open the following file using a text editor: jupyter_notebook_config.py
	d. Change the following line:

		| :code:`#c.NotebookApp.notebook_dir = u"`
		| to:
		| :code:`c.NotebookApp.notebook_dir = 'C:\Your\Path'`
		| Note: Be careful not to leave an empty space in the line when you delete the '#' character, the first character on that line is 'c'.

	e. Save the file
	f. Relaunch Anaconda Navigator
	g. Launch jupyter notebook

#. See the following link from Anaconda if you have a `proxy <https://docs.anaconda.com/anaconda/user-guide/tasks/proxy/>`_
#. See the following link from Anaconda if you have a `firewall <https://docs.anaconda.com/anaconda-enterprise-4/ae-and-nav/#configuring-firewall-settings>`_

