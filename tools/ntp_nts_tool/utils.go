package main

import (
	"encoding/json"
	"fmt"
	"strings"
	"time"
)

func time32ToSeconds(val uint32) float64 {
	intPart := val >> 16
	fracPart := val & 0xFFFF
	return float64(intPart) + float64(fracPart)/65536.0
}

func ntp64ToTime(ntp uint64) time.Time {
	// NTP epoch starts 1900, Unix starts 1970 -> difference is 2208988800s
	const ntpEpochOffset = 2208988800
	secs := int64(ntp >> 32)
	frac := float64(ntp&0xFFFFFFFF) / (1 << 32)
	return time.Unix(secs-int64(ntpEpochOffset), int64(frac*1e9))
}
func timeToNtpUint64(t time.Time) uint64 {
	const ntpEpochOffset = 2208988800
	secs := uint64(t.Unix() + ntpEpochOffset)
	frac := uint64((float64(t.Nanosecond()) / 1e9) * (1 << 32))
	return (secs << 32) | frac
}
func nowToNtpUint64() uint64 {
	t := time.Now()
	unixSec := t.Unix() // seconds since 1970-01-01
	unixNano := t.Nanosecond()
	ntpSec := uint64(unixSec + 2208988800)
	frac := uint64((float64(unixNano) / 1e9) * (1 << 32))
	return (ntpSec << 32) | frac
}
func ntp64ToFloatSeconds(ntp uint64) float64 {
	seconds := float64(ntp >> 32)                  // integer part
	frac := float64(ntp&0xFFFFFFFF) / 4294967296.0 // fractional part
	return seconds + frac
}

func printJson(server string, data map[string]interface{}) {
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		fmt.Println("Error converting to JSON:", err)
		return
	}
	fmt.Printf("NTPv5 response from %s:\n%s\n", server, string(jsonData))
}
func jsonToString(data map[string]interface{}, output *strings.Builder) {
	jsonData, err := json.MarshalIndent(data, "", "  ")
	if err != nil {
		output.WriteString(fmt.Sprintf("Error converting to JSON. Showing raw data\n%v\n", data))
		return
	}
	output.WriteString(string(jsonData))
}

//func jsonToStringWithError(data map[string]interface{}, output *strings.Builder) {
//	jsonData, err := json.MarshalIndent(data, "", "  ")
//	if err != nil {
//		output.WriteString(fmt.Sprintf("Error converting to JSON. Showing raw data\n%v\n", data))
//		return
//	}
//	output.WriteString(string(jsonData))
//}
