from ipaddress import IPv6Address, IPv4Address, ip_address

import numpy as np

from server.app.models.NtpExtraDetails import NtpExtraDetails
from server.app.models.NtpMainDetails import NtpMainDetails
from server.app.models.NtpMeasurement import NtpMeasurement
from server.app.models.NtpServerInfo import NtpServerInfo
from server.app.models.NtpTimestamps import NtpTimestamps
from server.app.models.PreciseTime import PreciseTime
from server.app.services.NtpCalculator import NtpCalculator
from server.app.services.NtpValidation import NtpValidation


def test_calculate_float_time():
    t = PreciseTime(10000, 2 ** 29)
    assert round(NtpCalculator.calculate_float_time(t), 8) == 10000 + 2 ** (-3)


def test_same_time():
    t = PreciseTime(10000, 10000)
    times = NtpTimestamps(t, t, t, t)
    assert NtpCalculator.calculate_offset(times) == 0.0
    assert NtpCalculator.calculate_delay(times) == 0.0


def test_different_times_offset():
    t1 = PreciseTime(10000, 0)
    t2 = PreciseTime(10002, 2 ** 27)
    t3 = PreciseTime(10003, 10000)
    t4 = PreciseTime(10004, 10000)
    times = NtpTimestamps(t1, t2, t3, t4)
    # 2^26/2^32=2^-6
    assert round(NtpCalculator.calculate_offset(times), 14) == 0.5 + 2 ** (-6)


def test_different_times_delay():
    t1 = PreciseTime(10000, 0)
    t2 = PreciseTime(10002, 0)
    t3 = PreciseTime(10003, 0)
    t4 = PreciseTime(10004, 2 ** 27)
    times = NtpTimestamps(t1, t2, t3, t4)
    # 2^27/2^32=2^-5
    assert round(NtpCalculator.calculate_delay(times), 14) == 3 - 2 ** (-5)


def test_create_object():
    vantage_point_ip = ip_address('127.0.0.1')
    t1 = PreciseTime(10000, 0)
    t2 = PreciseTime(10002, 2 ** 27)
    t3 = PreciseTime(10003, 10000)
    t4 = PreciseTime(10004, 10000)
    server_details = NtpServerInfo(3, IPv4Address('192.0.2.1'), "local", IPv6Address('2001:db8::1'), "reference")
    times = NtpTimestamps(t1, t2, t3, t4)
    maindetails = NtpMainDetails(0.009, 0, 1, 0, "stable")
    extra = NtpExtraDetails(PreciseTime(100000, 0), PreciseTime(100000, 0), 0)
    extra_invalid = NtpExtraDetails(PreciseTime(100000, 0), PreciseTime(100000, 0), 3)

    measurements = NtpMeasurement(vantage_point_ip, server_details, times, maindetails, extra)

    assert NtpValidation.is_valid(measurements.extra_details) == True
    assert NtpValidation.is_valid(extra_invalid) == False


def test_no_jitter():
    assert NtpCalculator.calculate_jitter([]) == 0.0
    assert NtpCalculator.calculate_jitter([0.02]) == 0.0

def test_jitter_two_offsets():
    offsets = [0.02, 0.01]
    assert NtpCalculator.calculate_jitter(offsets) == np.absolute(0.02 - 0.01)

def test_jitter_equal_offsets():
    offsets = [0.5, 0.5, 0.5, 0.5]
    assert NtpCalculator.calculate_jitter(offsets) == 0.0

def test_jitter_different_offsets():
    offsets = [0.0023, 0.0019, 0.0025, 0.0021, 0.0024]
    result = NtpCalculator.calculate_jitter(offsets)
    expected = ((0.0019 - 0.0023) ** 2 + (0.0025 - 0.0023) ** 2 +
                (0.0021 - 0.0023) ** 2 + (0.0024 - 0.0023) ** 2) / 4
    expected = expected ** 0.5
    assert result == expected

def test_jitter_negative_offsets():
    offsets = [-0.002, -0.001, -0.003]
    result = NtpCalculator.calculate_jitter(offsets)
    expected = ((-0.001 + 0.002)**2 + (-0.003 + 0.002)**2) / 2
    expected = expected ** 0.5
    assert result == expected