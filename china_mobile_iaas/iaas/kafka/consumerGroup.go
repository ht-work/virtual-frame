package kafka

import (
	"github.com/Shopify/sarama"
	"golang.org/x/net/context"
	"iaas/pkgs/config"
	"os"
	"os/signal"
	"strings"
	"sync"
	"syscall"
	"time"
)

var (
	//k config.KafkaConfig
	kc      = config.Conf.Kafka
	log     = config.Log
	chAlert = make(chan *sarama.ConsumerMessage, 1)
	chMoni  = make(chan *sarama.ConsumerMessage, 1)
	chCmdb  = make(chan *sarama.ConsumerMessage, 1)
)

type KfkConsumer struct {
	MessageQueue chan string
}

func (k *KfkConsumer) ConsumerGroup() {
	kc := config.Conf.Kafka
	//kc := config.KafkaList[0]
	c := sarama.NewConfig()

	version, err := sarama.ParseKafkaVersion("2.1.1")
	if err != nil {
		log.Errorln("Error parsing Kafka version:", err)
	}

	c.Version = version
	c.Consumer.Group.Rebalance.Strategy = sarama.BalanceStrategyRange
	c.Consumer.Offsets.Initial = sarama.OffsetOldest

	consumer := Consumer{
		ready: make(chan bool),
	}

	ctx, cancel := context.WithCancel(context.Background())
	client, err := sarama.NewConsumerGroup(strings.Split(kc.Brokers, ","), kc.ConsumerGroup, c)
	if err != nil {
		log.Fatalln("Error creating consumer group client: %v", err)
	}

	wg := &sync.WaitGroup{}
	wg.Add(1)
	go func() {
		defer wg.Done()
		for {
			//if err := client.Consume(ctx, kc.Topics.TopList, &consumer); err != nil {
			if err := client.Consume(ctx, strings.Split(kc.TopicList, ","), &consumer); err != nil {
				log.Fatalln("Error from consumer: %v", err)
			}
			// check if context was cancelled, signaling that the consumer should stop
			if ctx.Err() != nil {
				return
			}
			consumer.ready = make(chan bool)
		}
	}()

	<-consumer.ready // Await till the consumer has been set up
	log.Info("Sarama consumer up and running!...")

	sigterm := make(chan os.Signal, 1)
	signal.Notify(sigterm, syscall.SIGINT, syscall.SIGTERM)
	select {
	case <-ctx.Done():
		log.Info("terminating: context cancelled")
	case <-sigterm:
		log.Info("terminating: via signal")
	}
	cancel()
	wg.Wait()
	if err = client.Close(); err != nil {
		log.Panicf("Error closing client: %v", err)
	}
}

// Consumer represents a Sarama consumer group consumer
type Consumer struct {
	ready chan bool
}

// Setup is run at the beginning of a new session, before ConsumeClaim
func (consumer *Consumer) Setup(sarama.ConsumerGroupSession) error {
	// Mark the consumer as ready
	close(consumer.ready)
	return nil
}

// Cleanup is run at the end of a session, once all ConsumeClaim goroutines have exited
func (consumer *Consumer) Cleanup(sarama.ConsumerGroupSession) error {
	return nil
}

// ConsumeClaim must start a consumer loop of ConsumerGroupClaim's Messages().
func (consumer *Consumer) ConsumeClaim(session sarama.ConsumerGroupSession, claim sarama.ConsumerGroupClaim) error {
	for message := range claim.Messages() {
		log.Debugln("Message claimed: topic = %s", message.Topic)
		time.Sleep(100 * time.Millisecond)

		switch message.Topic {
		case kc.Topics.Cmdb:
			go UpgradeCMDB()
			chCmdb <- message
		case kc.Topics.Alert:
			go UpgradeAlert()
			chAlert <- message
		default:
			go UpgradeMonitor()
			chMoni <- message
		}
	}
	return nil
}
