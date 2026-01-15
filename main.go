package main

import (
	"bufio"
	"fmt"
	"net"
	"os"
)

func main() {
	// RECEIVER MODE (iPhone)
	if len(os.Args) == 1 {
		port := ":8080"
		ln, err := net.Listen("tcp", port)
		if err != nil {
			fmt.Printf("Error starting listener: %v\n", err)
			return
		}
		fmt.Printf("iPhone is listening on %s...\n", port)

		for {
			conn, err := ln.Accept()
			if err != nil {
				fmt.Printf("Error accepting connection: %v\n", err)
				continue // Don't crash, just wait for the next attempt
			}

			// Handle the connection
			go func(c net.Conn) {
				defer c.Close()
				fmt.Printf("\n[Incoming connection from %s]\n", c.RemoteAddr())

				reader := bufio.NewReader(c)
				message, err := reader.ReadString('\n')
				if err != nil {
					fmt.Printf("Error reading message: %v\n", err)
					return
				}
				fmt.Printf("Received: %s", message)
			}(conn)
		}
	}

	// SENDER MODE (Mac)
	if len(os.Args) > 1 {
		target := os.Args[1] + ":8080"
		fmt.Printf("Connecting to %s...\n", target)

		conn, err := net.Dial("tcp", target)
		if err != nil {
			fmt.Printf("Could not connect to iPhone: %v\n", err)
			return
		}
		defer conn.Close()

		fmt.Print("Enter message: ")
		text, _ := bufio.NewReader(os.Stdin).ReadString('\n')

		_, err = fmt.Fprintf(conn, text)
		if err != nil {
			fmt.Printf("Failed to send: %v\n", err)
		} else {
			fmt.Println("Message sent successfully!")
		}
	}
}
