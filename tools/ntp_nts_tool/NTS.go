package main

import (
	"crypto/tls"
	"fmt"
	"net"
	"os"
	"strings"
	"time"

	"github.com/beevik/nts"
)

// Serban Orza modifications
// usages: <host>
//         <host_ip>
//         <host> ipv4/ipv6 (what IP you want if possible)

//OBS: if you measure directly an IP, then the TLS certificate is not validated (because this tool does not know to
//which domain name this IP belongs)

//return/error codes meaning:
// 0 -> ok, NTS measurement succeeded
// 1 -> KE failed
// 2 -> DNS problem, "Could not deduct NTP host and port"
// 3 -> KE succeeded, but measurement timeout
// 4 -> invalid NTP response (it violates the RFC rules)
// 5 -> KE succeeded, but KissCode detected
// 6 -> NTS measurement succeeded, but not on the wanted IP family (ex: domain name NTS only works on ipv4)

//So 0 and 6 mean the measurement succeeded. (6 has a warning)

var usage_info_for_nts = `Usage:
	<host>
	<host_ip>
	<host> ipv4/ipv6 (what IP you want if possible)
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
*/

func measureNTS(args []string) {
	//args := os.Args[1:]

	if len(args) < 1 || len(args) > 2 {
		fmt.Println("invalid commands")
		fmt.Println(usage_info_for_nts)
		os.Exit(0)
	} else if len(args) == 1 {
		is_ip := net.ParseIP(args[0])
		result, err_code := "", 0
		if is_ip == nil { //is a domain name
			result, err_code = measureDomainName(args[0])
		} else { //is an IP address
			result, err_code = measureSpecificIP(args[0])
		}
		fmt.Print(result)
		os.Exit(err_code)
	} else if len(args) == 2 && (args[1] == "ipv6" || args[1] == "ipv4") {
		//firstly test if this domain name is NTS. Then try to get the wanted IP
		result, err_code := measureDomainName(args[0])
		if err_code == 0 {
			//now we now the domain name is NTS. Try to get the wanted IP family
			//wait a bit to not scary the NTS server
			time.Sleep(500 * time.Millisecond)
			result_ip_family, err_code_ip_family := measureDomainNameWithIPFamily(args[0], args[1])
			if err_code_ip_family == 0 {
				//success, we got the wanted IP family
				fmt.Print(result_ip_family)
				os.Exit(err_code_ip_family)
			} else {
				//fail. return the initial result
				fmt.Print("Wanted ip type failed.\n")
				fmt.Print(result)
				os.Exit(6)
			}
		} else {
			//the domain name is not NTS
			fmt.Print(result)
			os.Exit(err_code)
		}
	}
	//invalid command
	//result, err_code := measureSpecificIP(args[0])
	fmt.Println("invalid commands")
	fmt.Println(usage_info_for_nts)
	os.Exit(-1)
}

func measureDomainNameWithIPFamily(hostname string, ip_family string) (string, int) {
	//ip_family is the IP family that you would prefer to get. If the request cannot be fulfilled, then it will return
	//the IP family that works (or none)
	var output strings.Builder
	dialer := &net.Dialer{
		Timeout: 7 * time.Second,
	}

	var network string
	if ip_family == "ipv6" {
		network = "tcp6"
	} else {
		network = "tcp4"
	}

	session, err := nts.NewSessionWithOptions(hostname, &nts.SessionOptions{
		TLSConfig: &tls.Config{
			ServerName: hostname,
			MinVersion: tls.VersionTLS13,
		},
		Dialer: func(_, addr string, tlsConfig *tls.Config) (*tls.Conn, error) {
			return tls.DialWithDialer(dialer, network, addr, tlsConfig)
		},
	})

	if err != nil {
		return fmt.Sprintf("NTSS session could not be established: key exchange failure %v\n", err.Error()), 1
	}

	measured_host_ip, port, err := net.SplitHostPort(session.Address())
	if err != nil {
		return fmt.Sprintf("Could not deduct NTP host and port: %v\n", err.Error()), 2
	}
	output.WriteString(fmt.Sprintf("Address family: %s\n", ip_family))

	return run_query_and_build_nts_result(&output, hostname, measured_host_ip, port, session)
}

func measureDomainName(hostname string) (string, int) {

	var output strings.Builder
	session, err := nts.NewSession(hostname)
	if err != nil {
		return fmt.Sprintf("NTS session could not be established: key exchange failure %v\n", err.Error()), 1
	}

	measured_host_ip, port, err := net.SplitHostPort(session.Address())
	if err != nil {
		output.WriteString(fmt.Sprintf("Could not deduct NTP host and port: %v\n", err.Error()))
		return output.String(), 2
	}

	return run_query_and_build_nts_result(&output, hostname, measured_host_ip, port, session)

}

func measureSpecificIP(ip string) (string, int) {

	var output strings.Builder
	session, err := nts.NewSessionWithOptions(ip, &nts.SessionOptions{
		TLSConfig: &tls.Config{
			ServerName:         ip,
			MinVersion:         tls.VersionTLS13,
			InsecureSkipVerify: true,
		},
		Dialer: func(network, addr string, tlsConfig *tls.Config) (*tls.Conn, error) {
			return tls.Dial("tcp", ip+":4460", tlsConfig)
		},
	})
	if err != nil {
		return "NTS session could not be established: key exchange failure\n", 1
	}
	measured_host_ip, port, _ := net.SplitHostPort(session.Address())

	if measured_host_ip != ip {
		output.WriteString(fmt.Sprintf("different_IP: True\n"))
		output.WriteString(fmt.Sprintf("Warning: KE wanted a different IP:%s? True\n", measured_host_ip))
	}

	return run_query_and_build_nts_result(&output, ip, measured_host_ip, port, session)
}

func run_query_and_build_nts_result(output *strings.Builder, host string, measured_host_ip string, port string, session *nts.Session) (string, int) {

	t1_time := time.Now() //nowToNtpUint64()
	r, err := session.Query()
	if err != nil {
		return "KE succeeded, but measurement timeout\n", 3
	}
	t4_time := time.Now() //nowToNtpUint64()
	t3_time := r.Time
	t2_time := t1_time.Add((t3_time.Sub(t4_time) + 2*r.ClockOffset))
	output.WriteString(fmt.Sprintf("Host: %s\n", host))
	output.WriteString(fmt.Sprintf("Measured server IP: %s\n", measured_host_ip)) //do not change "Measured server IP". See nts_check.py if you want to change it.
	output.WriteString(fmt.Sprintf("Measured server port: %s\n", port))
	output.WriteString(fmt.Sprintf("version: %v\n", r.Version))
	output.WriteString(fmt.Sprintf("RefID_raw: 0x%08x\n", r.ReferenceID))
	output.WriteString(fmt.Sprintf("RefID: %s\n", r.ReferenceString()))

	output.WriteString(fmt.Sprintf("client_sent_time: %v\n", timeToNtpUint64(t1_time))) //t1
	output.WriteString(fmt.Sprintf("server_recv_time: %v\n", timeToNtpUint64(t2_time))) //t2
	output.WriteString(fmt.Sprintf("server_sent_time: %v\n", timeToNtpUint64(r.Time)))  //t3
	output.WriteString(fmt.Sprintf("client_recv_time: %v\n", timeToNtpUint64(t4_time))) //t4

	output.WriteString(fmt.Sprintf("        RTT: %v\n", r.RTT))
	output.WriteString(fmt.Sprintf("     Offset: %v\n", r.ClockOffset))
	output.WriteString(fmt.Sprintf("  Precision: %v\n", r.Precision))
	output.WriteString(fmt.Sprintf("    Stratum: %v\n", r.Stratum))

	output.WriteString(fmt.Sprintf("  RootDelay: %v\n", r.RootDelay))
	output.WriteString(fmt.Sprintf("       Poll: %v\n", r.Poll))
	output.WriteString(fmt.Sprintf("   RootDisp: %v\n", r.RootDispersion))
	output.WriteString(fmt.Sprintf("    RefTime: %v\n", r.ReferenceTime))
	output.WriteString(fmt.Sprintf("   RootDist: %v\n", r.RootDistance))
	output.WriteString(fmt.Sprintf("Leap: %v\n", r.Leap))
	output.WriteString(fmt.Sprintf("   KissCode: %v\n", sanities(r.KissCode)))
	output.WriteString(fmt.Sprintf("   MinError: %v\n", r.MinError))

	err = r.Validate()
	if err != nil {
		output.WriteString(fmt.Sprintf("\nInvalid NTP response: %v\n", err.Error()))
		return output.String(), 4
	}

	if r.KissCode != "" {
		output.WriteString(fmt.Sprintf("KE succeeded, but KissCode: %s\n", r.KissCode))
		return output.String(), 5
	}
	return output.String(), 0
}

func sanities(s string) string {
	if s == "" {
		return "None"
	}
	return s
}
