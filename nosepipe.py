"""Plugin for the nose testing framework for running tests in a subprocess.

Use ``nosetests --with-process-isolation`` to enable the plugin.  When enabled,
each test is run in a separate process.

Copyright 2007 John J. Lee <jjl@pobox.com>
"""

import os
import pickle
import struct
import subprocess
import sys

import nose.plugins

__version__ = "0.3"

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

    def configure(self, options, conf):
        if not self.can_configure:
            return
        self.conf = conf
        self.enabled = '--with-' + self.name in sys.argv

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
    def __init__(self, test):
        self._test = test

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
        argv = [os.path.abspath(sys.argv[0]),
                '--with-process-isolation-reporter',
                test_name]
        popen = subprocess.Popen(argv,
                                 cwd=os.getcwd(),
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT,
                                 )
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

    def configure(self, options, config):
        nose.plugins.Plugin.configure(self, options, config)

    def prepareTestCase(self, test):
        self._test = test
        self._test_proxy = SubprocessTestProxy(test)
        return self._test_proxy

    def afterTest(self, test):
        self._test_proxy = None
        self._test = None
