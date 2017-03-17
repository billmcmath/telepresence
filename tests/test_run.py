"""
End-to-end tests for running directly in the operating system.
"""

from unittest import TestCase
from subprocess import check_output, Popen
import time

from .utils import DIRECTORY, random_name


class EndToEndTests(TestCase):
    """
    End-to-end tests.
    """

    def test_tocluster(self):
        """
        Tests of communication to the cluster.

        Python script is run using telepresence --run, and output is
        checked for the string "SUCCESS!" indicating the checks passed. The
        script shouldn't use code py.test would detect as a test.
        """
        result = str(
            check_output([
                "telepresence",
                "--new-deployment",
                random_name(),
                "--run",
                "python3",
                "tocluster.py",
            ], cwd=str(DIRECTORY)), "utf-8")
        assert "SUCCESS!" in result

    def test_fromcluster(self):
        """
        Tests of communication from the cluster.

        Start webserver that serves files from this directory. Run HTTP query
        against it on the Kubernetes cluster, compare to real file.
        """
        name = random_name()
        p = Popen(
            [
                "telepresence", "--new-deployment", name,
                "--expose", "8080", "--run",
                "python3", "-m", "http.server", "8080"
            ], cwd=str(DIRECTORY))

        def cleanup():
            p.terminate()
            p.wait()

        self.addCleanup(cleanup)
        time.sleep(30)
        result = check_output([
            'kubectl', 'run', '--attach', random_name(), '--generator=job/v1',
            "--quiet", '--rm', '--image=alpine', '--restart', 'Never',
            '--command', '--', '/bin/sh', '-c',
            "apk add --no-cache --quiet curl && " +
            "curl http://{}:8080/__init__.py".format(name)
        ])
        assert result == (DIRECTORY / "__init__.py").read_bytes()

    # XXX write test for IP-based routing, not just DNS-based routing!
