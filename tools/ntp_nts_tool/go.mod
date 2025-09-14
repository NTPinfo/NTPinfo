module ntp_nts_tool

go 1.24.0

require (
	github.com/beevik/ntp v1.4.3
	github.com/beevik/nts v0.2.1
)

require (
	github.com/aead/cmac v0.0.0-20160719120800-7af84192f0b1 // indirect
	github.com/secure-io/siv-go v0.0.0-20180922214919-5ff40651e2c4 // indirect
	golang.org/x/net v0.44.0 // indirect
	golang.org/x/sys v0.36.0 // indirect
)

//replace golang.org/x/net => golang.org/x/net v0.30.0
//replace golang.org/x/sys => golang.org/x/sys v0.26.0
