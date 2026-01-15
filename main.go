package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
)

func main() {
	// 1. Check if we should be a Sender or Receiver
	if len(os.Args) == 1 {
		startReceiver()
	} else {
		startSender(os.Args[1])
	}
}

func startReceiver() {
	ln, err := net.Listen("tcp4", ":8080")
	if err != nil {
		fmt.Printf("Fatal Listener Error: %v\n", err)
		return
	}
	fmt.Println("Listening on port 8080...")

	for {
		conn, err := ln.Accept()
		if err != nil {
			// This is where it was failing before!
			fmt.Printf("Accept failed (probably accept4 error): %v\n", err)
			continue
		}

		// SAFETY: Only read if conn is NOT nil
		if conn != nil {
			go handleConn(conn)
		}
	}
}

func handleConn(conn net.Conn) {
	defer conn.Close()
	message, err := bufio.NewReader(conn).ReadString('\n')
	if err != nil {
		return
	}
	fmt.Printf("Incoming: %s", message)
}

func startSender(ip string) {
	conn, err := net.Dial("tcp4", ip+":8080")
	if err != nil {
		fmt.Printf("Connection Failed: %v\n", err)
		return
	}
	defer conn.Close()

	fmt.Print("Message: ")
	msg, _ := bufio.NewReader(os.Stdin).ReadString('\n')
	fmt.Fprintf(conn, msg)
	fmt.Println("Sent!")
}
