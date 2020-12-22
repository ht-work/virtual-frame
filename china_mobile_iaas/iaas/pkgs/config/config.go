package config

import (
	"fmt"
	"github.com/syssam/go-validator"
	"gopkg.in/yaml.v2"
	"io/ioutil"
	"os"
	"path/filepath"
)

const (
	EnvKeyConfigFile = "CONFIG_FILE"
	EnvKeyDebug      = "DEBUG"
)

var (
	Conf *Config = &Config{}
	//KafkaList []*KafkaConfig
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
	MaxConnLifeTime  int    `yaml:"maxConLifeTime"`
}

type KafkaConfig struct {
	Topics        Topics `yaml:"topics" valid:"required"`
	Brokers       string `yaml:"brokers" valid:"required"`
	ConsumerGroup string `yaml:"consumer_group" valid:"required"`
	TopicList     string `yaml:"topic_list"`
	//Sasl          bool   `yaml:"sasl"`
	//SaslUser      string `yaml:"sasl_user"`
	//SaslPasswd    string `yaml:"sasl_password"`
	//Tls           bool   `yaml:"tls"`
	//Cert          string `yaml:"cert"`
	//Key           string `yaml:"key"`
	//Ca            string `yaml:"ca"`
}

type Topics struct {
	Cmdb    string `yaml:"cmdb"`
	Alert   string `yaml:"alert"`
	Monitor string `yaml:"monitor"`
	Topics  string `yaml:"topics"`
	TopList []string
}

type Prometheus struct {
	PromServer   string `yaml:"server"`
	PromPort     string `yaml:"port"`
	PromUri      string `yaml:"uri"`
	PromUriRange string `yaml:"uri_range"`
}

type Config struct {
	ListenAddr  string         `yaml:"listenAddr" valid:"required"`
	ListUrl     string         `yaml:"list_url" valid:"required"`
	Token       string         `yaml:"token" valid:"required"`
	DetailUrl   string         `yaml:"detail_url" valid:"required"`
	MonitorUrl  string         `yaml:"monitor_url" valid:"required"`
	Database    DatabaseConfig `yaml:"database" valid:"required"`
	Kafka       KafkaConfig    `yaml:"kafka" valid:"required"`
	LogLevel    int            `yaml:"log_level"`
	InitWholeData bool         `yaml:"init_whole_data"`
	*Prometheus `yaml:"prometheus"`
}

func init() {
	Log = Conf.GetLogger()
	ParseArgs()
	var configFile string
	if e, ok := os.LookupEnv(EnvKeyConfigFile); ok {
		configFile = filepath.Clean(e)
	}

	if configFile == "" {
		env := os.Getenv("env")
		if env == "" || env == "iaas" {
			configFile = "/etc/iaas/config/iaas/config.yaml"
		} else {
			configFile = fmt.Sprintf("/etc/iaas/config/iaas-%s/config.yaml", env)
		}
	}

	configData, err := ioutil.ReadFile(configFile)
	if err != nil {
		Log.Panic("parse config file err: %w", err)
	}

	if err := yaml.Unmarshal(configData, Conf); err != nil {
		Log.Panic("read config file err %w", err)
	}

	if err := validator.ValidateStruct(Conf); err != nil {
		Log.Panic("check config file err: %w", err)
	}

	if Conf.Kafka.Topics.Alert != "" {
		Conf.Kafka.Topics.TopList = append(Conf.Kafka.Topics.TopList, Conf.Kafka.Topics.Alert)
	}
	if Conf.Kafka.Topics.Monitor != "" {
		Conf.Kafka.Topics.TopList = append(Conf.Kafka.Topics.TopList, Conf.Kafka.Topics.Monitor)
	}
	if Conf.Kafka.Topics.Cmdb != "" {
		Conf.Kafka.Topics.TopList = append(Conf.Kafka.Topics.TopList, Conf.Kafka.Topics.Cmdb)
	}
}
