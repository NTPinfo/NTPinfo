package main

// This file was inspired from David Marco's project: ntptools
// In this project (NTPinfo), we only needed the NTS tool, so we took some code from Marco and modified it to fit in our project


import (
	"crypto/tls"
	"fmt"
	"net"
	"os"
	"time"
	"github.com/beevik/nts"
)


// Serban Orza modifications
// usages: <host>
//         <host> <wanted_host_Ip>

//OBS: if you measure directly an IP, than the TLS certificate is not validated (because this tool does not know to
//which domain name this IP belongs)

//return/error codes meaning:
// 0 -> ok, NTS measurement succeeded
// 1 -> KE failed
// 2 -> DNS problem, "Could not deduct NTP host and port"
// 3 -> KE succeeded, but measurement timeout
// 4 -> invalid NTP response (it violates the RFC rules)
// 5 -> KE succeeded, but KissCode detected

func main() {
	args := os.Args[1:]

	if len(args) < 1 {
		fmt.Println("needs more arguments")
		os.Exit(0)
	} else if len(args) == 1 {
		measureDomainName(args[0]) //also with TLS certificate validation
	} else {
		measureSpecificIP(args[0], args[1])
	}
}

func measureDomainName(host string) {

	session, err := nts.NewSession(host)
	if err != nil {
		fmt.Printf("NTS session could not be established: key exchange failure\n")
        os.Exit(1)
    }

    measured_host, port, err := net.SplitHostPort(session.Address())
	if err != nil {
        fmt.Printf("Could not deduct NTP host and port: %v\n", err.Error())
        os.Exit(2)
    }

    fmt.Printf("\n\n --------------------------- \n")
    fmt.Printf("Host: %s\n", host)
    fmt.Printf("Measured server IP: %s\n", measured_host)
    fmt.Printf("Measured server port: %s\n", port)
	r, err := session.Query();
	if err != nil {
		fmt.Printf("KE succeeded, but measurement timeout")
		os.Exit(3)
	}
	fmt.Printf("  LocalTime: %v\n", time.Now())
	fmt.Printf("   XmitTime: %v\n", r.Time)
	fmt.Printf("    RefTime: %v\n", r.ReferenceTime)
	fmt.Printf("        RTT: %v\n", r.RTT)
	fmt.Printf("     Offset: %v\n", r.ClockOffset)
	fmt.Printf("       Poll: %v\n", r.Poll)
	fmt.Printf("  Precision: %v\n", r.Precision)
	fmt.Printf("    Stratum: %v\n", r.Stratum)
	fmt.Printf("      RefID: 0x%08x\n", r.ReferenceID)
	fmt.Printf("  RootDelay: %v\n", r.RootDelay)
	fmt.Printf("   RootDisp: %v\n", r.RootDispersion)
	fmt.Printf("   RootDist: %v\n", r.RootDistance)
	fmt.Printf("   MinError: %v\n", r.MinError)
	fmt.Printf("       Leap: %v\n", r.Leap)
	fmt.Printf("   KissCode: %v\n", stringOrEmpty(r.KissCode))

	err = r.Validate()
	if err != nil {
		fmt.Printf("\nError: %v\n", err.Error())
		os.Exit(4)
	}

    if r.KissCode != "" {
		fmt.Printf("KE succeeded, but KissCode: %s", r.KissCode)
		os.Exit(5)
    }

	fmt.Printf("\n\n")
}

func measureSpecificIP(hostname string, ip string) {
    fmt.Printf("args: %s %s?\n", hostname, ip)
    session, err := nts.NewSessionWithOptions(hostname, &nts.SessionOptions{
        TLSConfig: &tls.Config{
            ServerName: hostname, // must match certificate
            MinVersion: tls.VersionTLS13,
            InsecureSkipVerify: true,
        },
        Dialer: func(network, addr string, tlsConfig *tls.Config) (*tls.Conn, error) {
            return tls.Dial("tcp", ip+":4460", tlsConfig)
        },
    })
	if err != nil {
		//fmt.Printf("NTS session could not be established: %v\n", err.Error())
		fmt.Printf("NTS session could not be established: key exchange failure\n")
		os.Exit(1)
	}
	measured_host, port, _ := net.SplitHostPort(session.Address())

    fmt.Printf("\n\n --------------------------- \n")
    fmt.Printf("Host: %s\n", hostname)

    if measured_host != ip {
        fmt.Printf("different_IP: True\n")
        fmt.Printf("Warning: KE wanted a different IP:%s? True\n", measured_host)
    }

    fmt.Printf("Measured server IP: %s\n", measured_host) //do not change "Measured server IP". See nts_check.py if you want to change it.
    fmt.Printf("Measured server port: %s\n", port)
	r, err := session.Query();
	if err != nil {
		fmt.Printf("KE succeeded, but measurement timeout")
		os.Exit(3)
	}

    fmt.Printf("  LocalTime: %v\n", time.Now())
	fmt.Printf("   XmitTime: %v\n", r.Time)
	fmt.Printf("    RefTime: %v\n", r.ReferenceTime)
	fmt.Printf("        RTT: %v\n", r.RTT)
	fmt.Printf("     Offset: %v\n", r.ClockOffset)
	fmt.Printf("       Poll: %v\n", r.Poll)
	fmt.Printf("  Precision: %v\n", r.Precision)
	fmt.Printf("    Stratum: %v\n", r.Stratum)
	fmt.Printf("      RefID: 0x%08x\n", r.ReferenceID)
	fmt.Printf("  RootDelay: %v\n", r.RootDelay)
	fmt.Printf("   RootDisp: %v\n", r.RootDispersion)
	fmt.Printf("   RootDist: %v\n", r.RootDistance)
	fmt.Printf("   MinError: %v\n", r.MinError)
	fmt.Printf("       Leap: %v\n", r.Leap)
	fmt.Printf("   KissCode: %v\n", stringOrEmpty(r.KissCode))

	err = r.Validate()
	if err != nil {
		fmt.Printf("\nError: %v\n", err.Error())
		os.Exit(4)
	}
    if r.KissCode != "" {
		fmt.Printf("KE succeeded, but KissCode: %s", r.KissCode)
		os.Exit(5)
    }

	fmt.Printf("\n\n")
}
func stringOrEmpty(s string) string {
	if s == "" {
		return "none"
	}
	return s
}
