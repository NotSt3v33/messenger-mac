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
	// 'tcp4' is the key to avoiding iSH networking errors
	ln, err := net.Listen("tcp4", ":8080")
	if err != nil {
		fmt.Printf("Startup Error: %v\n", err)
		return
	}
	fmt.Println("Listening on port 8080... (Waiting for Mac)")

	for {
		conn, _ := ln.Accept()
		message, _ := bufio.NewReader(conn).ReadString('\n')
		fmt.Printf("Incoming: %s", message)
		conn.Close()
	}
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
