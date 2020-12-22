package main

import (
	"iaas/kafka"
	"iaas/pkgs/config"
	"iaas/pkgs/rest"
	"iaas/web"
	"os"
	"os/signal"
	"syscall"
)

func main() {
	// initial and run app
	var app = &web.App{}
	app.Config = config.Conf

	// Terminal web server
	env := os.Getenv("env")
	if env == "" || env == "iaas" {
		go app.Start()
	}

	// Terminal kafka full recode
	rest.Run()

	// Terminal kafka consumer
	go func() {
		consumer := kafka.KfkConsumer{}
		consumer.ConsumerGroup()
	}()

	// Terminal handler
	term := make(chan os.Signal)
	signal.Notify(term, os.Interrupt, syscall.SIGTERM, syscall.SIGQUIT)
	<-term
	os.Exit(0)
}
