//go:build linux && 386

package main

import (
	"syscall"
	_ "unsafe"
)

// This hijacks the internal function Go uses for all TCP accepts.
// By pointing it to our local version, we bypass the accept4 requirement.
//
//go:linkname pollAccept4Func internal/poll.Accept4Func
var pollAccept4Func func(int, int) (int, syscall.Sockaddr, error)

func init() {
	// We replace the broken Accept4 with a custom wrapper
	// that only uses the basic Accept.
	pollAccept4Func = func(fd, flags int) (int, syscall.Sockaddr, error) {
		return syscall.Accept(fd)
	}
}
