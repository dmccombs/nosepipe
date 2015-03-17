"""Plugin for the nose testing framework for running tests in a subprocess.

Use ``nosetests --with-process-isolation`` to enable the plugin.  When enabled,
each test is run in a separate process.

Copyright 2007 John J. Lee <jjl@pobox.com>
"""

import logging
import os
import pickle
import struct
import subprocess
import sys

import nose.plugins

__version__ = "0.7"

SUBPROCESS_ENV_KEY = "NOSE_WITH_PROCESS_ISOLATION_REPORTER"


class NullWritelnFile(object):
    def write(self, *arg):
        pass

    def writelines(self, *arg):
        pass

    def close(self, *arg):
        pass

    def flush(self, *arg):
        pass

    def isatty(self, *arg):
        return False

    def writeln(self, *arg):
        pass


class Code(object):
    def __init__(self, code):
        self.co_filename = code.co_filename
        self.co_name = code.co_name


class Frame(object):
    def __init__(self, frame):
        self.f_globals = {"__file__": frame.f_globals["__file__"]}
        self.f_code = Code(frame.f_code)


class Traceback(object):
    def __init__(self, tb):
        self.tb_frame = Frame(tb.tb_frame)
        self.tb_lineno = tb.tb_lineno
        if tb.tb_next is None:
            self.tb_next = None
        else:
            self.tb_next = Traceback(tb.tb_next)


class ProcessIsolationReporterPlugin(nose.plugins.Plugin):

    """Part of the internal mechanism for ProcessIsolationPlugin.

    Reports test progress over the pipe to the parent process.
    """

    name = "process-isolation-reporter"

    def setOutputStream(self, stream):
        # we use stdout for IPC, so block all other output
        self._stream = sys.__stdout__
        return NullWritelnFile()

    def startTest(self, test):
        self._send_test_event("startTest", test)

    def addError(self, test, err):
        self._send_test_event("addError", test, err)

    def addFailure(self, test, err):
        self._send_test_event("addFailure", test, err)

    def addSuccess(self, test):
        self._send_test_event("addSuccess", test)

    def stopTest(self, test):
        self._send_test_event("stopTest", test)

    def _send_test_event(self, method_name, test, err=None):
        if err is not None:
            exc_pickle = pickle.dumps(
                self._fake_exc_info(err)).decode("latin1")
            data = "%s:%s" % (method_name, exc_pickle)
        else:
            data = method_name

        data = data.encode("latin1")
        header = struct.pack("!I", len(data))

        # Try writing bytes first (Python 3) and fall back to string (Python 2)
        try:
            self._stream.buffer.write(header + data)
        except AttributeError:
            self._stream.write(header + data)

        self._stream.flush()

    def _fake_exc_info(self, exc_info):
        # suitable for pickling
        exc_type, exc_value = exc_info[:2]
        return exc_type, exc_value, Traceback(exc_info[2])


class SubprocessTestProxy(object):
    def __init__(self, test, argv, cwd):
        self._test = test
        self._argv = argv
        self._cwd = cwd
        self.logger = logging.getLogger('nose.plugins.process_isolation')

    def _name_from_address(self, address):
        filename, module, call = address
        if filename is not None:
            if filename[-4:] in [".pyc", ".pyo"]:
                filename = filename[:-1]
            head = filename
        else:
            head = module
        if call is not None:
            return "%s:%s" % (head, call)
        return head

    def __call__(self, result):
        test_name = self._name_from_address(self._test.address())
        argv = self._argv + [test_name]
        useshell = False

        # Shell should be used on Windows since this is likely executing a
        # script rather than an exe, but shell can cause problems on other
        # operating systems. 'win32' is also 64-bit Windows.
        if sys.platform == 'win32':
            useshell = True

        self.logger.debug("Executing %s", " ".join(argv))
        try:
            popen = subprocess.Popen(argv,
                                     cwd=self._cwd,
                                     stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT,
                                     shell=useshell,
                                     )
        except OSError as e:
            raise Exception("Error running %s [%s]" % (argv[0], e))

        try:
            stdout = popen.stdout
            while True:
                header = stdout.read(4)
                if not header:
                    break
                if len(header) < 4:
                    raise Exception("short message header %r" % header)
                request_len = struct.unpack("!I", header)[0]
                data = stdout.read(request_len)
                if len(data) < request_len:
                    raise Exception("short message body (want %d, got %d)\n" %
                                    (request_len, len(data)) +
                                    "Something went wrong\nMessage: %s" %
                                    (header + data).decode("latin1"))
                data = data.decode("latin1")
                parts = data.split(":", 1)
                if len(parts) == 1:
                    method_name = data
                    getattr(result, method_name)(self._test)
                else:
                    method_name, exc_pickle = parts
                    exc_info = pickle.loads(exc_pickle.encode("latin1"))
                    getattr(result, method_name)(self._test, exc_info)
        finally:
            popen.wait()


class ProcessIsolationPlugin(nose.plugins.Plugin):

    """Run each test in a separate process."""

    name = "process-isolation"

    def __init__(self):
        nose.plugins.Plugin.__init__(self)
        self._test = None
        self._test_proxy = None

        # Normally, nose is called as:
        #     nosetests {opt1} {opt2} ...
        # However, we can also be run as:
        #     setup.py nosetests {opt1} {opt2} ...
        # When not running directly as nosetests, we need to run the
        # sub-processes as `nosetests`, not `setup.py nosetests` as the output
        # of setup.py interferes with the nose output.  So, we need to find
        # where nosetests is on the command-line and then run the
        # sub-processes command-line using the args from that location.

        nosetests_index = None
        # Find where nosetests is in argv and start the new argv from there
        # in case we're running as something like `setup.py nosetests`
        for i in range(0, len(sys.argv)):
            if 'nosetests' in sys.argv[i]:
                self._argv = [sys.argv[i]]
                nosetests_index = i
                break

        # If we can't find nosetests in the command-line we must be running
        # from some other test runner like django's `manage.py test`.  Replace
        # the runner with `nosttests` and proceed...
        if nosetests_index is None:
            nosetests_index = 0
            self._argv = ['nosetests']

        self._argv += ['--with-process-isolation-reporter']
        # add the rest of the args that appear in argv after `nosetests`
        self._argv += ProcessIsolationPlugin._get_nose_whitelisted_argv(
            offset=nosetests_index + 1)
        # Getting cwd inside SubprocessTestProxy.__call__ is too late - it is
        # already changed by nose
        self._cwd = os.getcwd()

    @staticmethod
    def _get_nose_whitelisted_argv(offset=1):
        # This is the list of nose options which should be passed through to
        # the launched process; boolean value defines whether the option
        # takes a value or not.
        #
        # offset: int, the argv index of the first nosetests option.
        #
        whitelist = {
            '--debug-log': True,
            '--logging-config': True,
            '--no-byte-compile': False,
            '--nologcapture': False,
            '--logging-format': True,
            '--logging-datefmt': True,
            '--logging-filter': True,
            '--logging-clear-handlers': False,
            '--logging-level': True,
            '--with-coverage': False,
            '--cover-package': True,
            '--cover-tests': False,
            '--cover-min-percentage': True,
            '--cover-inclusive': False,
            '--cover-branches': False,
            '--no-deprecated': False,
            '--with-doctest': False,
            '--doctest-tests': False,
            '--doctest-extension': True,
            '--doctest-result-variable': True,
            '--doctest-fixtures': True,
            '--doctest-options': True,
            '--no-skip': False,
        }
        filtered = set(whitelist.keys()).intersection(set(sys.argv[offset:]))
        result = []
        for key in filtered:
            result.append(key)
            if whitelist[key]:
                result.append(sys.argv[sys.argv.index(key) + 1])

        # We are not finished yet: options with '=' were not handled
        whitelist_keyval = [(k + "=") for k, v in whitelist.items() if v]
        for arg in sys.argv[offset:]:
            for keyval in whitelist_keyval:
                if arg.startswith(keyval):
                    result.append(arg)
        return result

    def options(self, parser, env):
        nose.plugins.Plugin.options(self, parser, env)
        env_opt = 'NODE_WITH_PROCESS_ISOLATION_INDIVIDUAL'
        parser.add_option('--with-process-isolation-individual',
                          action='store_true',
                          help='Run only selected tests in separate '+
                          'processes [%s].' % env_opt,
                          default=env.get(env_opt))

    def configure(self, options, config):
        self.individual = options.with_process_isolation_individual
        nose.plugins.Plugin.configure(self, options, config)
        try:
            if self.enabled and options.enable_plugin_coverage:
                from coverage import coverage

                def nothing(*args, **kwargs):
                    pass

                # Monkey patch coverage to fix the reporting and friends
                coverage.start = nothing
                coverage.stop = nothing
                coverage.combine = nothing
                coverage.save = coverage.load
        except:
            pass

    def do_isolate(self, test):
        # XXX is there better way to access 'nosepipe_isolate'?
        if not self.individual:
            return True
        if hasattr(test.test, 'nosepipe_isolate'):
            return True
        if hasattr(test.test, 'test') \
           and hasattr(test.test.test, 'nosepipe_isolate'):
            return True

    def prepareTestCase(self, test):
        if self.do_isolate(test):
            self._test = test
            self._test_proxy = SubprocessTestProxy(test, self._argv, self._cwd)
            return self._test_proxy

    def afterTest(self, test):
        self._test_proxy = None
        self._test = None


def isolate(obj):
    '''Mark testcase as isolated in separate process.'''
    setattr(obj, 'nosepipe_isolate', True)
    return obj
