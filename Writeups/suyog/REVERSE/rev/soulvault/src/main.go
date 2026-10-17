package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"
)

func printBanner() {
	fmt.Println("╔══════════════════════════════════════════╗")
	fmt.Println("║               SOUL VAULT                 ║")
	fmt.Println("║      Secure Key Verification System      ║")
	fmt.Println("║               Version 3.4.1              ║")
	fmt.Println("╚══════════════════════════════════════════╝")
	fmt.Println()
}

func main() {
	printBanner()

	fmt.Println("Enter access sequence:")
	fmt.Print("> ")

	reader := bufio.NewReader(os.Stdin)
	input, err := reader.ReadString('\n')
	if err != nil && len(input) == 0 {
		fmt.Println("[-] Error reading input stream.")
		os.Exit(1)
	}

	input = strings.TrimSpace(input)
	if len(input) == 0 {
		fmt.Println("[-] Empty sequence provided.")
		os.Exit(1)
	}

	ok, message := ProcessAccessSequence(input)
	fmt.Println()
	fmt.Println(message)

	if !ok {
		os.Exit(1)
	}
}
