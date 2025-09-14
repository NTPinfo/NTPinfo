package main

import (
	"crypto/tls"
	"fmt"
	"net"
	"os"
	"strconv"
	"strings"
	"time"

	//"github.com/SerbanOrza/nts"
	"github.com/beevik/nts"

	"github.com/beevik/ntp"
)

// Serban Orza modifications

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

var usage_info_for_nts = `If you want to use NTS commands, you can use:
	<host>
    <host> <timeout_s>
    <host_ip>
    <host_ip> <timeout_s>
    <host> ipv4/ipv6     (what IP type you want if possible. If not, you will get the type that is available for NTS)
    <host> ipv4/ipv6 <timeout_s>
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

	timeout := float64(7) //by default
	if len(args) < 1 || len(args) > 3 {
		fmt.Println("invalid nts commands")
		fmt.Println(usage_info_for_nts)
		os.Exit(-100)
	} else if len(args) == 1 {
		is_ip := net.ParseIP(args[0])
		result, err_code := "", 0
		if is_ip == nil { //is a domain name
			result, err_code = measureDomainName(args[0], timeout)
		} else { //is an IP address
			result, err_code = measureSpecificIP(args[0], timeout)
		}
		fmt.Println(result)
		os.Exit(err_code)
	} else if args[1] == "ipv6" || args[1] == "ipv4" {
		if len(args) == 3 {
			timeout_new, err := strconv.ParseFloat(args[2], 64)
			if err != nil {
				fmt.Println("timeout needs to be a number (int or float)")
				os.Exit(-100)
			}
			timeout = timeout_new
		}
		//firstly test if this domain name is NTS. Then try to get the wanted IP
		result, err_code := measureDomainName(args[0], timeout)
		if err_code == 0 {
			//now we now the domain name is NTS. Try to get the wanted IP family
			//wait a bit to not scary the NTS server
			time.Sleep(500 * time.Millisecond)
			result_ip_family, err_code_ip_family := measureDomainNameWithIPFamily(args[0], args[1], timeout)
			if err_code_ip_family == 0 {
				//success, we got the wanted IP family
				fmt.Println(result_ip_family)
				os.Exit(err_code_ip_family)
			} else {
				//fail. return the initial result
				//fmt.Print("Wanted ip type failed.\n")
				fmt.Println(result)
				os.Exit(6)
			}
		} else {
			//the domain name is not NTS
			fmt.Println(result)
			os.Exit(err_code)
		}
	} else if len(args) == 2 {
		//timeout included
		timeout_new, err := strconv.ParseFloat(args[1], 64)
		if err != nil {
			fmt.Println("timeout needs to be a number (int or float)")
			os.Exit(-100)
		}
		timeout = timeout_new
		is_ip := net.ParseIP(args[0])
		result, err_code := "", 0
		if is_ip == nil { //is a domain name
			result, err_code = measureDomainName(args[0], timeout)
		} else { //is an IP address
			result, err_code = measureSpecificIP(args[0], timeout)
		}
		fmt.Println(result)
		os.Exit(err_code)
	}
	//invalid command
	//result, err_code := measureSpecificIP(args[0])
	fmt.Println("invalid commands")
	fmt.Println(usage_info_for_nts)
	os.Exit(-100)
}

func measureDomainNameWithIPFamily(hostname string, ip_family string, timeout float64) (string, int) {
	//ip_family is the IP family that you would prefer to get. If the request cannot be fulfilled, then it will return
	//the IP family that works (or none)
	var output strings.Builder
	dialer := &net.Dialer{
		Timeout: time.Duration(timeout) * time.Second,
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
		Timeout: time.Duration(timeout) * time.Second, //a bit redundant as it is also included in Dialer (but is safe)
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
	//output.WriteString(fmt.Sprintf("Address family: %s\n", ip_family))

	return run_query_and_build_nts_result(&output, hostname, measured_host_ip, port, session, timeout)
}

func measureDomainName(hostname string, timeout float64) (string, int) {

	var output strings.Builder
	//session, err := nts.NewSession(hostname)
	session, err := nts.NewSessionWithOptions(hostname, &nts.SessionOptions{
		Timeout: time.Duration(timeout) * time.Second,
	})
	if err != nil {
		return fmt.Sprintf("NTS session could not be established: key exchange failure %v\n", err.Error()), 1
	}

	measured_host_ip, port, err := net.SplitHostPort(session.Address())
	if err != nil {
		output.WriteString(fmt.Sprintf("Could not deduct NTP host and port: %v\n", err.Error()))
		return output.String(), 2
	}

	return run_query_and_build_nts_result(&output, hostname, measured_host_ip, port, session, timeout)

}

func measureSpecificIP(ip string, timeout float64) (string, int) {

	var output strings.Builder
	session, err := nts.NewSessionWithOptions(ip, &nts.SessionOptions{
		TLSConfig: &tls.Config{
			ServerName:         ip,
			MinVersion:         tls.VersionTLS13,
			InsecureSkipVerify: true,
		},
		Timeout: time.Duration(timeout) * time.Second,
		Dialer: func(network, addr string, tlsConfig *tls.Config) (*tls.Conn, error) {
			return tls.Dial("tcp", ip+":4460", tlsConfig)
		},
	})
	if err != nil {
		return "NTS session could not be established: key exchange failure\n", 1
	}
	measured_host_ip, port, _ := net.SplitHostPort(session.Address())

	if measured_host_ip != ip {
		//output.WriteString(fmt.Sprintf("different_IP: True\n"))
		output.WriteString(fmt.Sprintf("Warning: KE wanted a different IP:%s? True\n", measured_host_ip))
	}

	return run_query_and_build_nts_result(&output, ip, measured_host_ip, port, session, timeout)
}

func run_query_and_build_nts_result(output *strings.Builder, host string, measured_host_ip string, port string,
	session *nts.Session, timeout float64) (string, int) {

	t1_time := time.Now() //nowToNtpUint64()
	r, err := safeQueryWithOptions(session, timeout)
	if err != nil {
		return fmt.Sprintf("KE succeeded, but measurement failed: %v\n", err), 3
	}
	if r == nil {
		return fmt.Sprintf("KE succeeded, but measurement failed. Received null or a too short response\n"), 3

	}
	//r, err := session.QueryWithOptions(&ntp.QueryOptions{
	//	Timeout: time.Duration(timeout) * time.Second,
	//})
	//if err != nil {
	//	return "KE succeeded, but measurement timeout\n", 3
	//}
	t4_time := time.Now() //nowToNtpUint64()
	t3_time := r.Time
	t2_time := t1_time.Add((t3_time.Sub(t4_time) + 2*r.ClockOffset))

	ke_wants_diff_ip_str := output.String() //get the info about different IP requested by Key Exchange (KE)
	output.Reset()
	//output.WriteString(fmt.Sprintf("Host: %s\n", host))
	//output.WriteString(fmt.Sprintf("Measured server IP: %s\n", measured_host_ip)) //do not change "Measured server IP". See nts_check.py if you want to change it.
	//output.WriteString(fmt.Sprintf("Measured server port: %s\n", port))
	//output.WriteString(fmt.Sprintf("version: %v\n", r.Version))
	//output.WriteString(fmt.Sprintf("RefID_raw: 0x%08x\n", r.ReferenceID))
	//output.WriteString(fmt.Sprintf("RefID: %s\n", r.ReferenceString()))
	//
	//output.WriteString(fmt.Sprintf("client_sent_time: %v\n", t1_time)) //t1
	//output.WriteString(fmt.Sprintf("server_recv_time: %v\n", t2_time)) //t2
	//output.WriteString(fmt.Sprintf("server_sent_time: %v\n", r.Time))  //t3
	//output.WriteString(fmt.Sprintf("client_recv_time: %v\n", t4_time)) //t4
	//
	//output.WriteString(fmt.Sprintf("        RTT: %v\n", r.RTT))
	//output.WriteString(fmt.Sprintf("     Offset: %v\n", r.ClockOffset))
	//output.WriteString(fmt.Sprintf("  Precision: %v\n", r.Precision))
	//output.WriteString(fmt.Sprintf("    Stratum: %v\n", r.Stratum))
	//
	//output.WriteString(fmt.Sprintf("RootDelay: %v\n", r.RootDelay))
	//output.WriteString(fmt.Sprintf("Poll: %v\n", r.Poll))
	//output.WriteString(fmt.Sprintf("RootDisp: %v\n", r.RootDispersion))
	//output.WriteString(fmt.Sprintf("RefTime: %v\n", r.ReferenceTime))
	//output.WriteString(fmt.Sprintf("RootDist: %v\n", r.RootDistance))
	//output.WriteString(fmt.Sprintf("Leap: %v\n", r.Leap))
	//output.WriteString(fmt.Sprintf("KissCode: %v\n", sanities(r.KissCode)))
	//output.WriteString(fmt.Sprintf("MinError: %v\n", r.MinError))

	info := map[string]interface{}{
		"Host":                 host,
		"Measured server IP":   measured_host_ip,
		"Measured server port": port,
		"version":              r.Version,
		"ref_id_raw":           fmt.Sprintf("0x%08x", r.ReferenceID),
		"ref_id":               r.ReferenceString(),
		"client_sent_time":     timeToNtpUint64(t1_time),
		"server_recv_time":     timeToNtpUint64(t2_time),
		"server_sent_time":     timeToNtpUint64(r.Time),
		"client_recv_time":     timeToNtpUint64(t4_time),
		"rtt":                  r.RTT.Seconds(),
		"offset":               r.ClockOffset.Seconds(),
		"precision":            r.Precision.Seconds(),
		"stratum":              r.Stratum,
		"mode":                 4,
		"root_delay":           r.RootDelay.Seconds(),
		"poll":                 r.Poll.Seconds(),
		"root_disp":            r.RootDispersion.Seconds(),
		"ref_time":             timeToNtpUint64(r.ReferenceTime),
		"root_dist":            r.RootDistance.Seconds(),
		"leap":                 r.Leap,
		"kissCode":             r.KissCode,
		"minError":             r.MinError.Seconds(),
		//"NTS_analysis":         "",
	}
	if ke_wants_diff_ip_str != "" {
		//this can be seen when measuring a specific IP address, but the results are shown with another IP
		info["warning_KE_wanted_diff_ip"] = "The measurement succeeded, but KE redirected us to another IP"
	}
	//info["0_pretty_data"] = fmt.Sprintf(output.String())
	err = r.Validate()
	//if everything is fine -> return the data with code 0
	//else -> return the error message with the specific error code
	if err != nil {
		output.WriteString(fmt.Sprintf("Invalid NTP response received: %v\n", err.Error()))
		//info["NTS_analysis"] = fmt.Sprintf("Invalid NTP response received: %v\n", err.Error())
		return output.String(), 4
	}

	if r.KissCode != "" {
		output.WriteString(fmt.Sprintf("KE succeeded, but KissCode: %s\n", r.KissCode))
		//info["NTS_analysis"] = fmt.Sprintf("KE succeeded, but KissCode: %s\n", r.KissCode)
		return output.String(), 5
	}
	//fmt.Println(output.String())
	var json_output strings.Builder
	//json_output.WriteString(output.String())
	//json_output.WriteString("\n")
	//info["NTS_analysis"] = "Measurement succeeded!"
	jsonToString(info, &json_output)
	return json_output.String(), 0
}

func safeQueryWithOptions(session *nts.Session, timeout float64) (*ntp.Response, error) {
	var r *ntp.Response
	var err error

	defer func() {
		if rec := recover(); rec != nil {
			err = fmt.Errorf("NTS library panic: %v", rec)
			r = nil
		}
	}()

	r, err = session.QueryWithOptions(&ntp.QueryOptions{
		Timeout: time.Duration(timeout) * time.Second,
	})

	if r == nil && err == nil {
		err = fmt.Errorf("NTS query returned nil response")
	}

	return r, err
}
