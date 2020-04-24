Using Gro API behind a Corporate Proxy
#######################################

The Gro API uses the requests package to communicate with the Gro Servers. If you are behind a corporate proxy, you may see the error message below:
 
.. code-block:: python

	requests.exceptions.ProxyError: HTTPSConnectionPool … (Caused by ProxyError('Cannot connect to proxy.', OSError('Tunnel connection failed: 407 Proxy Authentication Required')))

Set an Environment Variable
===========================

Note: The variables in the examples below should be replaced with the actual values for your environment.

Windows
-------

To change environment variables on Windows:

#. In the Start menu, search for “env”.
#. Select “Edit Environment Variables for your account”
#. Select “Environment Variables…”
#. Press “New…”
#. Add two variables :code:`http_proxy` and :code:`https_proxy` both with the same value depending on the type of proxy:
   
   #. Unauthenticated Proxy:
      ::
        http_proxy="http://your-proxy-domain:<port>"
        https_proxy="http://your-proxy-domain:<port>"
	
	
   #. Authenticated Proxy:
      ::
        http_proxy="http://username:password@corp.com:<port>"
        https_proxy="http://username:password@corp.com:<port>"
 
MacOS / Linux
--------------

You can set an environment variable for temporary or permanent use. If you need a variable for just one time, you can set it up using terminal.

#. Temporarily change the environment variables by running :code:`export variable_name=variable_value` from the terminal prompt depending on the type of proxy:
   
   #. Unauthenticated Proxy:
      ::
        export http_proxy="http://your-proxy-domain:<port>"
        export https_proxy="http://your-proxy-domain:<port>"
	
	
   #. Authenticated Proxy:
      ::
        export http_proxy="http://username:password@corp.com:<port>"
        export https_proxy="http://username:password@corp.com:<port>"
	
#. Permanently change the environment variables in MacOS.  For permanent setting, you need to understand where to put the “export” command. This is determined by what shell you are using. You can check this by running the following command: :code:`echo $SHELL` 
   
   #. /bin/bash:  Edit  ~/.bash_profile and add the following lines based on the type of proxy:
      
      #. Unauthenticated Proxy:
         ::
	   export http_proxy="http://your-proxy-domain:<port>"
	   export https_proxy="http://your-proxy-domain:<port>"
      
      
      #. Authenticated Proxy:
         ::
           export http_proxy="http://username:password@corp.com:<port>"
	   export https_proxy="http://username:password@corp.com:<port>"
	
   #. /bin/zsh:   Edit  ~/.zshrc and add the following lines based on the type of proxy:
      
      #. Unauthenticated Proxy:
         ::
           export http_proxy="http://your-proxy-domain:<port>"
	   export https_proxy="http://your-proxy-domain:<port>"
	
	
      #. Authenticated Proxy:
         ::
           export http_proxy="http://username:password@corp.com:<port>"
	   export https_proxy="http://username:password@corp.com:<port>"
