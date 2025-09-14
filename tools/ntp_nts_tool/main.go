package main

import (
	"fmt"
	"os"
	"strconv"
)

var usage_info = `Usage:
    nts <host>
    nts <host> <timeout_s>
    nts <host_ip>
    nts <host_ip> <timeout_s>
    nts <host> ipv4/ipv6     (what IP type you want if possible. If not, you will get the type that is available for NTS)
    nts <host> ipv4/ipv6 <timeout_s>

    <NTP_version> <host>
    <NTP_version> <host> <timeout_s>
    <NTP_version> <host_ip>
    <NTP_version> <host_ip> <timeout_s>

where:
	- <NTP_version> can be ntpv1,ntpv2,ntpv3,ntpv4,ntpv5
	- host_ip it can be both ipv4 or ipv6
	- timeout_s is a float64 in seconds. By default it is 7 seconds in both NTP and NTS
`

/*
Return codes for measuring NTS:

	    0 -> ok, NTS measurement succeeded
		1 -> KE failed
		2 -> DNS problem, "Could not deduct NTP host and port"
		3 -> KE succeeded, but measurement timeout
		4 -> invalid NTP response (it violates the RFC rules)
		5 -> KE succeeded, but KissCode detected
		6 -> NTS measurement succeeded, but not on the wanted IP family (ex: domain name NTS only works on ipv4)

OBS: 0 and 6 mean the measurement succeeded. (6 has a warning)
OBS: if you measure directly an IP, then the TLS certificate is not validated (because this tool does not know to

	which domain name this IP belongs)

Return codes for measuring NTP:

		-100 -> commands is malformed
		0 -> success, measurement performed. See results on screen
	    1 -> error connecting to the server
	    2 -> could not send data to the connection with the server
	    3 -> measurement timeout
	    4 -> error parsing response

Warning:
 1. In both cases (NTP and NTS) where you use a domain name as the host, consider that this tool does not resolve
    the domain name in terms of the client IP. It resolves the domain name based on the machine that executes this code.
    If you want to use an IP address (for server) near the client, then resolve it somewhere else and use that IP in this code.
    (The aim of this tool is to perform NTP and NTS measurement, not to solve DNS problems)
 2. In NTS measurements performed on a specific IP address, KE may redirect to another IP address. If this is the case, a warning
    will be shown in the response. The measurement succeeded, but KE redirected us to another IP. (you can also see this in
    host vs measured server ip
*/
func main() {
	//server := "2001:4860:4806:c::" //"time.cloudflare.com" //"time.apple.com" //"ntp0.testdns.nl" //"ntp0.testdns.nl" //"time.apple.com"
	args := os.Args[1:]
	//server := "162.159.200.1" //"time.cloudflare.com" //args := os.Args[1:]
	//args := []string{"nts", server, "1"}
	if len(args) < 1 || len(args) > 3 {
		fmt.Println(usage_info)
		os.Exit(-100)
	}
	if args[0] == "nts" {
		measureNTS(args[1:])
		os.Exit(0)
	}
	//ntp versions part
	timeout := float64(7)
	if len(args) == 3 {
		timeout_new, err := strconv.ParseFloat(args[2], 64)
		if err != nil {
			fmt.Println("timeout needs to be a number (int or float)")
			os.Exit(-100)
		}
		timeout = timeout_new
	}
	if args[0] == "ntpv1" {
		performNTPv1Measurement(args[1], timeout) //very unlikely to receive an answer as nobody supports ntpv1 anymore
	} else if args[0] == "ntpv2" {
		performNTPv3Measurement(args[1], timeout, 2) //same code as in 3 basically
	} else if args[0] == "ntpv3" {
		performNTPv3Measurement(args[1], timeout, 3)
	} else if args[0] == "ntpv4" {
		performNTPv4Measurement(args[1], timeout)
	} else if args[0] == "ntpv5" {
		performNTPv5Measurement(args[1], timeout)
	} else {
		fmt.Println("unknown command\n")
		fmt.Println(usage_info)
		os.Exit(-100)
	}
}
