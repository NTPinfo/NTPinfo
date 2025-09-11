package main

import (
	"bytes"
	"encoding/binary"
	"fmt"
	"math/rand"
	"net"
	"os"
	"strconv"
	"strings"
	"time"
)

const (
	NTPV5_VERSION = 5
	TIMESCALE_UTC = 0
	HEADER_SIZE   = 48
)

type NTPv5Header struct {
	LIVNMode       uint8 // LI(2) | VN(3) | Mode(3)
	Stratum        uint8
	Poll           int8
	Precision      int8
	Timescale      uint8
	Era            uint8
	Flags          uint16
	RootDelay      uint32
	RootDispersion uint32
	ServerCookie   uint64
	ClientCookie   uint64
	RecvTimestamp  uint64
	TxTimestamp    uint64
}

func decodeFlags(flags uint16) map[string]bool {
	return map[string]bool{
		"synchronized": flags&0x1 != 0,
		"interleaved":  flags&0x2 != 0,
		"auth_nak":     flags&0x4 != 0,
	}
}

func buildNTPv5Request() ([]byte, uint64) {
	clientCookie := rand.Uint64()
	buf := make([]byte, 48)

	// Byte 0: LI(2 bits) | VN(3 bits) | Mode(3 bits)
	buf[0] = (0 << 6) | (NTPV5_VERSION << 3) | 3

	// Byte 1: Stratum = 0
	buf[1] = 0
	// Byte 2: Poll = 0
	buf[2] = 0
	// Byte 3: Precision = 0
	buf[3] = 0
	// Byte 4: Timescale (UTC=0)
	buf[4] = 0
	// Byte 5: Era
	buf[5] = 0
	// Bytes 6-7: Flags (uint16)
	binary.BigEndian.PutUint16(buf[6:8], 0)
	// Bytes 8-11: Root Delay (uint32)
	binary.BigEndian.PutUint32(buf[8:12], 0)
	// Bytes 12-15: Root Dispersion (uint32)
	binary.BigEndian.PutUint32(buf[12:16], 0)

	// Bytes 16-23: Server Cookie (uint64)
	binary.BigEndian.PutUint64(buf[16:24], 0)
	// Bytes 24-31: Client Cookie (uint64)
	binary.BigEndian.PutUint64(buf[24:32], clientCookie)

	// Bytes 32-39: Recv Timestamp (uint64)
	binary.BigEndian.PutUint64(buf[32:40], 0)
	// Bytes 40-47: Tx Timestamp (uint64)
	binary.BigEndian.PutUint64(buf[40:48], 0)

	return buf, clientCookie
}

func parseNTPv5Response(data []byte, clientCookie uint64, clientSentTime float64) (map[string]interface{}, error) {
	if len(data) < HEADER_SIZE {
		return nil, fmt.Errorf("response too short")
	}

	header := NTPv5Header{}
	buf := bytes.NewReader(data[:HEADER_SIZE])
	if err := binary.Read(buf, binary.BigEndian, &header); err != nil {
		return nil, err
	}

	info := map[string]interface{}{
		"leap":                (header.LIVNMode >> 6) & 0x03,
		"version":             (header.LIVNMode >> 3) & 0x07,
		"mode":                header.LIVNMode & 0x07,
		"stratum":             header.Stratum,
		"poll":                header.Poll,
		"precision":           header.Precision,
		"timescale":           header.Timescale,
		"era":                 header.Era,
		"flags_raw":           header.Flags,
		"flags_decoded":       decodeFlags(header.Flags),
		"root_delay":          time32ToSeconds(header.RootDelay),      //in seconds
		"root_disp":           time32ToSeconds(header.RootDispersion), //in seconds
		"server_cookie":       header.ServerCookie,
		"client_cookie":       header.ClientCookie,
		"recv_timestamp":      header.RecvTimestamp,
		"tx_timestamp":        header.TxTimestamp,
		"client_cookie_valid": header.ClientCookie == clientCookie,
	}

	// Parse extension fields if any
	if len(data) > HEADER_SIZE {
		exts := []map[string]interface{}{}
		extData := data[HEADER_SIZE:]
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
	//add offset and rtt
	t1 := clientSentTime
	t2 := ntp64ToFloatSeconds(header.RecvTimestamp)
	t3 := ntp64ToFloatSeconds(header.TxTimestamp)
	t4 := ntp64ToFloatSeconds(nowToNtpUint64())

	info["offset_s"] = ((t2 - t2) + (t3 - t4)) / 2 //in seconds
	info["rtt_s"] = (t4 - t1) - (t3 - t2)          //in seconds
	return info, nil
}

func performNTPv5Measurement(server string, timeout float64) {

	var output strings.Builder
	//addr := fmt.Sprintf("%s:%d", server, NTP_PORT)
	addr := net.JoinHostPort(server, strconv.Itoa(123))

	conn, err := net.Dial("udp", addr)
	if err != nil {
		fmt.Printf("error connecting: %v", err)
		os.Exit(2)
	}
	defer conn.Close()

	t1 := ntp64ToFloatSeconds(nowToNtpUint64())
	req, client_cookie := buildNTPv5Request()
	_, err = conn.Write(req)
	if err != nil {
		fmt.Printf("error sending ntpv5 request: %v", err)
		os.Exit(2)
	}

	conn.SetReadDeadline(time.Now().Add(time.Duration(timeout) * time.Second))
	resp := make([]byte, 1024)
	n, err := conn.Read(resp)
	if err != nil {
		fmt.Printf("error reading response: %v", err)
		os.Exit(4)
	}

	result, err := parseNTPv5Response(resp[:n], client_cookie, t1)
	if err != nil {
		fmt.Printf("error parsing response: %v", err)
		os.Exit(4)
	}
	jsonToString(result, &output)
	fmt.Print(output.String())
	os.Exit(0)
}
