package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"net"
	"os"
	"strconv"
	"strings"

	//"ntp_nts_tool/utils"
	"time"
)

// NTPv4 constants
const (
	NTPV4_VERSION   = 4
	MODE_CLIENT     = 3
	NTP_PACKET_SIZE = 48
)

type NTPv4Header struct {
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

func buildNTPv4Request() ([]byte, float64) {
	req := make([]byte, NTP_PACKET_SIZE)

	// LI = 0 (no warning), VN = 4, Mode = 3 (client)
	req[0] = (0 << 6) | (NTPV4_VERSION << 3) | MODE_CLIENT

	t1 := nowToNtpUint64() //timeToNtp64(time.Now())
	binary.BigEndian.PutUint64(req[40:], t1)

	return req, ntp64ToFloatSeconds(t1)
}

func parseNTPv4Response(data []byte, t1 float64, t4 float64) (map[string]interface{}, error) {
	if len(data) < NTP_PACKET_SIZE {
		return nil, fmt.Errorf("response too short: %d bytes", len(data))
	}

	h := NTPv4Header{}
	buf := bytes.NewReader(data[:NTP_PACKET_SIZE])
	if err := binary.Read(buf, binary.BigEndian, &h); err != nil {
		return nil, err
	}

	t2 := ntp64ToFloatSeconds(h.RecvTimestamp)
	t3 := ntp64ToFloatSeconds(h.TxTimestamp)

	rtt := (t4 - t1) - (t3 - t2)
	offset := ((t2 - t2) + (t3 - t4)) / 2

	info := map[string]interface{}{ //same as NTPv3
		"leap":           (h.LIVNMode >> 6) & 0x03,
		"version":        (h.LIVNMode >> 3) & 0x07,
		"mode":           h.LIVNMode & 0x07,
		"stratum":        h.Stratum,
		"poll":           h.Poll,
		"precision":      h.Precision,
		"root_delay":     time32ToSeconds(h.RootDelay),
		"root_disp":      time32ToSeconds(h.RootDispersion),
		"ref_id":         h.RefID, //this may have a different meaning in NTPv4
		"ref_timestamp":  h.RefTimestamp,
		"orig_timestamp": h.OrigTimestamp,
		"recv_timestamp": h.RecvTimestamp,
		"tx_timestamp":   h.TxTimestamp,
		"rtt":            rtt,
		"offset":         offset,
	}

	// Check if there are extension fields after the 48-byte header
	if len(data) > NTP_PACKET_SIZE {
		fmt.Println("EXTRA FIELDDDDD")
		exts := []map[string]interface{}{}
		extData := data[NTP_PACKET_SIZE:]
		for len(extData) >= 4 {
			typ := binary.BigEndian.Uint16(extData[0:2])
			length := binary.BigEndian.Uint16(extData[2:4])
			if int(length) > len(extData) || length < 4 {
				break
			}
			payload := extData[4:length]
			exts = append(exts, map[string]interface{}{
				"type": typ,
				"data": payload,
			})
			extData = extData[length:]
		}
		info["extensions"] = exts
	}

	return info, nil
}

func performNTPv4Measurement(server string, timeout float64) {

	var output strings.Builder
	//addr := fmt.Sprintf("%s:%d", server, 123)
	addr := net.JoinHostPort(server, strconv.Itoa(123))

	conn, err := net.Dial("udp", addr)
	if err != nil {
		fmt.Printf("error connecting: %v", err)
		os.Exit(1)
	}
	defer conn.Close()

	req, t1 := buildNTPv4Request()
	_, err = conn.Write(req)
	if err != nil {
		fmt.Printf("could not send request: %v", err)
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
	result, err := parseNTPv4Response(resp[:n], t1, t4)

	if err != nil {
		fmt.Printf("error reading/parsing response: %v", err)
		os.Exit(4)
	}
	jsonToString(result, &output)
	fmt.Print(output.String())
	os.Exit(0)
}
