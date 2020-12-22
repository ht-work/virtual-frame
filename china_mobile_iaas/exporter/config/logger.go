package config

import (
"github.com/sirupsen/logrus"
"os"
)

var Log *logrus.Logger

func GetLogger() *logrus.Logger {
	var log = logrus.New()

	log.Out = os.Stdout
	log.SetFormatter(&logrus.TextFormatter{
		TimestampFormat: "2006-01-02 15:04:05",
		FullTimestamp: true,
	})
	log.SetLevel(logrus.DebugLevel)
	//switch c.LogLevel {
	//case 1:
	//	log.SetLevel(logrus.FatalLevel)
	//case 2:
	//	log.SetLevel(logrus.ErrorLevel)
	//case 3:
	//	log.SetLevel(logrus.WarnLevel)
	//case 4:
	//	log.SetLevel(logrus.InfoLevel)
	//case 5:
	//	log.SetLevel(logrus.DebugLevel)
	//default:
	//	log.SetLevel(logrus.InfoLevel)
	//}
	return log
}

