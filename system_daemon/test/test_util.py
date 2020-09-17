import sys

sys.path.insert(0, '..')
from sysagent.util import Verify


class TestUtilVerify(object):

    def test_is_ipv4_valid(self):
        ipv4 = '1.2.3.4'
        assert Verify.is_ipv4_valid(ipv4)

        ipv4 = 'sf.3^%f$#We'
        assert not Verify.is_ipv4_valid(ipv4)

    def test_is_hostname_valid(self):
        hostname = 'eX3_-.Ample'
        assert Verify.is_hostname_valid(hostname)

        hostname = 'ex ample'
        assert not Verify.is_hostname_valid(hostname)

        hostname = 'ex@ample'
        assert not Verify.is_hostname_valid(hostname)

        hostname = 'ex@am#$EW%$&*^%ple'
        assert not Verify.is_hostname_valid(hostname)
