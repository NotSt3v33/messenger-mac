//go:build linux && 386

package main

import (
	_ "unsafe"
	"syscall"
)

// This "re-links" the internal Go poll function to use a basic accept
//go:linkname accept4 syscall.accept4
func accept4(fd int, sa syscall.Sockaddr, flags int) (int, error) {
	// We ignore the 'flags' and just use the basic Accept
	return syscall.Accept(fd)
}
