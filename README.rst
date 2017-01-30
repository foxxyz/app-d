app-d: Automated Python Push-Deploy
===================================

Setting up a git push deployment target `isn't terribly difficult <http://krisjordan.com/essays/setting-up-push-to-deploy-with-git>`_, but it gets tedious if you do it often.

With **app-d**, creating new push-deploy setups becomes a little bit easier. In addition, app-d sets up a remote repository that other developers with group permissions can push and deploy to as well.

What Does it Do?
----------------

In short, app-d runs through the following steps:

* Connect to your remote server
* Add a group
* Add your user to the new group
* Create directories for the remote repository and the application itself
* Set correct permissions and handling ACL for these directories
* Install a post-receive hook for correct deployment

Requirements
------------

* Python 3.3+

Installation
------------

.. code-block:: bash
	
	$ pip install app-d

Usage
-----

Run ``app-d`` for an interactive version, or see ``app-d --help`` for CLI arguments.

License
-------

MIT