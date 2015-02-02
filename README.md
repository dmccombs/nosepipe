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

To use Nosepipe, add --with-process-isolation to your nosetests command and
decorate tests to be run separately:

    import nosepipe

    def test_something():
        # In subprocess
        pass

If --with-process-isolation-individual option is used in addition, then every
test (either a top-level function or a class) need to be decorated to be run in
a separate process.

    import nosepipe

    def test_something():
        # In main process
        pass

    class TestClass(unittest.TestCase):
        # In main process
        def test_something():
            pass

    @nosepipe.isolate
    def test_another():
        # In subprocess
        pass

    @nosepipe.isolate
    class AnotherTestClass(unittest.TestCase):
        # In subprocess
        def test_another():
            pass
