package config

import (
	"flag"
)

var TestMode int

const (
	PRODUCT = iota
	TEST
)

func ParseArgs() {
	var mode string

	flag.StringVar(&mode, "m", "product", "product: product env(default); test: test env")

	flag.Parse()

	switch mode {
	case "product":
		TestMode = PRODUCT
	case "test":
		TestMode = TEST
	default:
		TestMode = PRODUCT
	}
}
