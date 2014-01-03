Nosepipe
========

Nosepipe is a plugin for the nose testing framework for running tests in a
subprocess.

Nosepipe was originally written by John J. Lee <jjl@pobox.com> and updated by
Dan McCombs <dmccombs@dyn.com> to support newer Python versions.

It's available under the BSD license.

You can also install nosepipe via pip or find it on PyPI at:

https://pypi.python.org/pypi/nosepipe

Installing
========

You can install the latest git version by cloning the repository and running:

python ./setup.py install

Otherwise, you can install the latest released version from pip via:

pip install nosepipe

Usage
========

To use Nosepipe, simply add --with-process-isolation to your nosetests command.
When enabled, each test is run in a separate process.
