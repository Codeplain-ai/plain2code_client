package main

import (
	"fmt"
	"os"
	"os/exec"
	"strings"
	"testing"
)

func TestHelloWorld(t *testing.T) {
	cwd, err := os.Getwd()
	if err != nil {
		fmt.Printf("Error getting current working directory: %v\n", err)
	} else {
		fmt.Printf("Command will be executed in the current working directory: %s\n", cwd)
	}

	cmd := exec.Command("go", "run", "hello_world.go")
	output, err := cmd.CombinedOutput()
	if err != nil {
		t.Fatalf("Failed to run hello_world.go: %v", err)
	}

	expected := "hello, world"
	actual := strings.TrimSpace(string(output))
	if actual != expected {
		t.Errorf("Expected output '%s', but got '%s'", expected, actual)
	}
}
