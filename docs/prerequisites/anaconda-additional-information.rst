Anaconda Additional Information
###############################

#. If your username includes spaces, as is common on Windows systems, you are not allowed to install Anaconda in the default path (C:\Users\<your-username>\Anaconda3\)
	#. See this `Anaconda link <https://docs.anaconda.com/anaconda/user-guide/faq/#distribution-faq-windows-folder>`_ for additional information. 
#. If you install Anaconda outside of the default path, then you will need to update the config for the jupyter notebook default directory as outlined below:
	#. Go to the default path (C:\Users/\<your-username>)
	#. Open the .jupyter folder (pay attention to the ‘dot’ before the name)
	#. Open the following file using a text editor: jupyter_notebook_config.py
	#. Edit the following line
		:code:`#c.NotebookApp.notebook_dir = u"`
		change it to:
		:code:`c.NotebookApp.notebook_dir = 'C:\Your\Path'`
		Note: Be careful not to leave an empty space in the line when you delete the ‘#’ character, the first character on that line is ‘c’
	#. Save the file
	#. Relaunch Anaconda Navigator
	#. Launch jupyter notebook
#. See the following link from Anaconda if you have a `proxy <https://docs.anaconda.com/anaconda/user-guide/tasks/proxy/>`_
#. See the following link from Anaconda if you have a `firewall <https://docs.anaconda.com/anaconda-enterprise-4/ae-and-nav/#configuring-firewall-settings>`_

