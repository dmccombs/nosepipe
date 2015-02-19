Running tests in a subprocess
=============================

The plugin runs each test in a separate process.

XXX This doctest doesn't actually test that separate processes are
used!


    >>> import os.path, sys

    >>> import nose.plugins

    >>> import nosepipe

    >>> directory_with_tests = os.path.join(os.path.dirname(__file__),
    ...                                     "test-support")
    >>> plugins = [nosepipe.ProcessIsolationPlugin(),
    ...            nosepipe.ProcessIsolationReporterPlugin()]


Successful run:

    >>> nose.plugins.plugintest.run(
    ...     argv=["nosetests", "-v", "--with-process-isolation",
    ...           os.path.join(directory_with_tests, "passing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    passing_tests.passing_test_1 ... ok
    passing_tests.passing_test_2 ... ok
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 2 tests in ...s
    <BLANKLINE>
    OK


Failing run:

    >>> py = os.path.join(directory_with_tests, "failing", "failing_tests.py")
    >>> testname = py + ":failing_test"
    >>> nose.plugins.plugintest.run(
    ...     argv=["nosetests", "-v", "--with-process-isolation",
    ...           testname],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    failing_tests.failing_test ... FAIL
    <BLANKLINE>
    ======================================================================
    FAIL: failing_tests.failing_test
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    AssertionError
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    FAILED (failures=1)


Erroring run:

    >>> py = os.path.join(directory_with_tests, "failing", "failing_tests.py")
    >>> testname = py + ":erroring_test"
    >>> nose.plugins.plugintest.run(
    ...     argv=["nosetests", "-v", "--with-process-isolation",
    ...           testname],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF
    failing_tests.erroring_test ... ERROR
    <BLANKLINE>
    ======================================================================
    ERROR: failing_tests.erroring_test
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    Exception
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 1 test in ...s
    <BLANKLINE>
    FAILED (errors=1)


Multiple failing tests:

    >>> nose.plugins.plugintest.run(
    ...     argv=["nosetests", "-v", "--with-process-isolation",
    ...           os.path.join(directory_with_tests, "failing")],
    ...     plugins=plugins)
    ...     # doctest: +REPORT_NDIFF +ELLIPSIS
    failing_tests.erroring_test ... ERROR
    failing_tests.failing_test ... FAIL
    <BLANKLINE>
    ======================================================================
    ERROR: failing_tests.erroring_test
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    Exception
    <BLANKLINE>
    ======================================================================
    FAIL: failing_tests.failing_test
    ----------------------------------------------------------------------
    Traceback (most recent call last):
    ...
    AssertionError
    <BLANKLINE>
    ----------------------------------------------------------------------
    Ran 2 tests in ...s
    <BLANKLINE>
    FAILED (errors=1, failures=1)

Django nose:

   >>> import subprocess
   >>> import re

   >>> # run a command and return it's output or error output
   >>> def run_cmd(argv):
   ...     try:  # python 2.7+
   ...         output = subprocess.check_output(argv, stderr=subprocess.STDOUT).decode('ascii')
   ...     except subprocess.CalledProcessError as e:
   ...         output = "Error running:\n{0}\nOutput:\n{1}".format(argv, e.output)
   ...     except Exception as subprocess_e:
   ...         try:
   ...             useshell = False
   ...             if sys.platform == 'win32':
   ...                 useshell = True
   ...             popen = subprocess.Popen(argv,
   ...                   shell=useshell,
   ...                   stdout=subprocess.PIPE,
   ...                   stderr=subprocess.PIPE,
   ...             )
   ...             stdout, stderr = popen.communicate()
   ...             output = "{0}{1}".format(stderr, stdout)
   ...         except OSError as popen_e:
   ...             output = "Error running:\n{0}\nSubprocess Output:\n{1}\nPopen Output".format(
   ...                 argv, subprocess_e, popen_e)
   ...     return output

   >>> # find all .egg directories to add to the path (were installed by setup.py develop/test)
   >>> top_dir = os.getcwd()
   >>> eggs = []
   >>> iseggdir = re.compile('\.egg$')
   >>> for top, dirs, f in os.walk(top_dir):
   ...     for dir in dirs:
   ...         if iseggdir.search(dir):
   ...             eggs += [os.path.join(top, dir)]

   >>> django_dir = os.path.join(directory_with_tests, "django")
   >>> os.chdir(django_dir)
   >>> print(run_cmd(["env", 
   ...     "PYTHONPATH={0}".format(":".join(eggs)), 
   ...     "python", "manage.py", "test", "--verbosity=1"]))
   ...     # doctest: +REPORT_NDIFF +ELLIPSIS
   .
   ----------------------------------------------------------------------
   Ran 1 test in ...s
   <BLANKLINE>
   OK
   nosetests --verbose --with-process-isolation --verbosity=1
   Creating test database for alias 'default'...
   Destroying test database for alias 'default'...
   <BLANKLINE>
   >>> os.chdir(top_dir)
