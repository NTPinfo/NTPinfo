package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
	"os"
	"strconv"
	"strings"
	"time"
)

type NTPv3Header struct { //same as NTPv4
	LIVNMode       uint8 // LI (2) | VN (3) | Mode (3)
	Stratum        uint8
	Poll           int8
	Precision      int8
	RootDelay      uint32
	RootDispersion uint32
	RefID          uint32
	RefTimestamp   uint64
	OrigTimestamp  uint64
	RecvTimestamp  uint64
	TxTimestamp    uint64
}

func buildNTPv3or2Request(ntpversion int) ([]byte, float64) {
	req := make([]byte, NTP_PACKET_SIZE)

	// LI = 0 (no warning), VN = 2 or 3, Mode = 3 (client)
	req[0] = (0 << 6) | (3 << 3) | 3
	if ntpversion == 2 {
		req[0] = (0 << 6) | (2 << 3) | 3
	}

	t1 := nowToNtpUint64() //timeToNtp64(time.Now())
	binary.BigEndian.PutUint64(req[40:], t1)

	return req, ntp64ToFloatSeconds(t1)
}

func parseNTPv3Response(data []byte, t1 float64, t4 float64) (map[string]interface{}, error) {
	if len(data) < NTP_PACKET_SIZE {
		return nil, fmt.Errorf("response too short: %d bytes", len(data))
	}

	h := NTPv3Header{}
	buf := bytes.NewReader(data[:NTP_PACKET_SIZE])
	if err := binary.Read(buf, binary.BigEndian, &h); err != nil {
		return nil, err
	}

	t2 := ntp64ToFloatSeconds(h.RecvTimestamp)
	t3 := ntp64ToFloatSeconds(h.TxTimestamp)

	rtt := (t4 - t1) - (t3 - t2)
	offset := ((t2 - t2) + (t3 - t4)) / 2

	info := map[string]interface{}{
		"leap":           (h.LIVNMode >> 6) & 0x03,
		"version":        (h.LIVNMode >> 3) & 0x07,
		"mode":           h.LIVNMode & 0x07,
		"stratum":        h.Stratum,
		"poll":           h.Poll,
		"precision":      h.Precision,
		"root_delay":     time32ToSeconds(h.RootDelay),
		"root_disp":      time32ToSeconds(h.RootDispersion),
		"ref_id":         h.RefID,
		"ref_timestamp":  h.RefTimestamp,
		"orig_timestamp": h.OrigTimestamp,
		"recv_timestamp": h.RecvTimestamp,
		"tx_timestamp":   h.TxTimestamp,
		"rtt":            rtt,
		"offset":         offset,
	}

	return info, nil
}

func performNTPv3Measurement(server string, timeout float64, ntpversion int) {

	var output strings.Builder
	addr := net.JoinHostPort(server, strconv.Itoa(123))

	conn, err := net.Dial("udp", addr)
	if err != nil {
		fmt.Printf("error connecting: %v", err)
		os.Exit(1)
	}
	defer conn.Close()

	req, t1 := buildNTPv3or2Request(ntpversion)
	_, err = conn.Write(req)
	if err != nil {
		fmt.Printf("could not send data: %v", err)
		os.Exit(2)
	}

	conn.SetReadDeadline(time.Now().Add(time.Duration(timeout) * time.Second))
	resp := make([]byte, 1024)
	n, err := conn.Read(resp)
	if err != nil {
		fmt.Printf("measurement timeout: %v", err)
		os.Exit(3)
	}

	t4 := ntp64ToFloatSeconds(nowToNtpUint64())
	result, err := parseNTPv3Response(resp[:n], t1, t4)

	if err != nil {
		fmt.Printf("error parsing response: %v", err)
		os.Exit(4)
	}
	jsonToString(result, &output)
	fmt.Print(output.String())
	os.Exit(0)
}
