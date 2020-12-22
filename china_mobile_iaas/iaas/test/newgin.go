package test

import (
	"fmt"
	"gopkg.in/yaml.v2"
	"io/ioutil"
)

const (
	EnvKeyConfigFile = "CONFIG_FILE"
	EnvKeyDebug      = "DEBUG"
)

type DatabaseConfig struct {
	Driver           string `yaml:"driver" valid:"required"`
	User             string `yaml:"user" valid:"required"`
	Passwd           string `yaml:"password" valid:"required"`
	Host             string `yaml:"host" valid:"required"`
	Port             string `yaml:"port" valid:"required"`
	Network          string `yaml:"proto" valid:"required"`
	Db               string `yaml:"db" valid:"required"`
	MaxIdleConnCount int    `yaml:"maxIdleConnCount"`
	MaxConnLifeTime  string `yaml:"maxConLifeTime"`
}

type KafkaConfig struct {
	Topics        string `yaml:"topics" valid:"required"`
	Brokers       string `yaml:"brokers" valid:"required"`
	ConsumerGroup string `yaml:"consumer_group" valid:"required"`
}

type Config struct {
	ListenAddr string         `yaml:"listenAddr" valid:"required"`
	Database   DatabaseConfig `yaml:"database" valid:"required"`
	Kafka      KafkaConfig    `yaml:"kafka" valid:"required"`
}

func main() {
	c := &Config{}
	c.Init()
}

func (c *Config) Init() {
	var configFile string

	configFile = "config/config.yaml"

	configData, err := ioutil.ReadFile(configFile)
	if err != nil {
		fmt.Println("parse config file err: %w", err)
		panic(err)
	}

	if err := yaml.Unmarshal(configData, c); err != nil {
		fmt.Println("read config file err %w", err)
		panic(err)
	}
	fmt.Println(*c)
}