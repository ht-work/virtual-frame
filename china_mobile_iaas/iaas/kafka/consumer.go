package kafka

//func (k *KfkConsumer) Consumer() {
//	kc := config.Conf.Kafka
//	c := sarama.NewConfig()
//
//	if kc.Sasl {
//		c.Net.SASL.Enable = true
//		c.Net.SASL.User = kc.SaslUser
//		c.Net.SASL.Password = kc.SaslPasswd
//	}
//
//	if kc.Tls {
//		tlsConfig, err := genTLSConfig(kc.Ca, kc.Key, kc.Cert)
//		if err != nil {
//			fmt.Println("TLS gen err:", err)
//		}
//
//		c.Net.TLS.Enable = true
//		c.Net.TLS.Config = tlsConfig
//	}
//
//	fmt.Println(strings.Split(kc.Brokers, ","))
//	client, err := sarama.NewClient(strings.Split(kc.Brokers, ","), c)
//	if err != nil {
//		fmt.Println("kafka client create err:", err)
//	}
//	//fmt.Println(client)
//	consumer, err := sarama.NewConsumerFromClient(client)
//	if err != nil {
//		fmt.Println("kafka connect failed, err:", err)
//		return
//	}
//	//fmt.Println(consumer)
//	defer consumer.Close()
//
//	for _, topic := range config.Conf.Kafka.Topics.TopList {
//		fmt.Println(topic, "==================")
//		partitions, err := consumer.Partitions(topic)
//		if err != nil {
//			fmt.Println("get partition failed,err:", err)
//			return
//		}
//		go func() {
//			k.consumeTopic(partitions, topic, consumer)
//		}()
//		for {
//			msg := <-k.MessageQueue
//			fmt.Println(msg)
//		}
//	}
//}
//
//func (k *KfkConsumer) consumeTopic(partitions []int32, topic string, consumer sarama.Consumer) {
//	fmt.Println("partitions:", partitions, "topic:", topic)
//	for _, p := range partitions {
//		partitionConsumer, err := consumer.ConsumePartition(topic, p, sarama.OffsetOldest)
//		if err != nil {
//			fmt.Printf("get topic %s partition %d consumer failed,err:%s\n", topic, p, err)
//			continue
//		}
//
//		fmt.Println("partitionConsumer:", partitionConsumer)
//		for message := range partitionConsumer.Messages() {
//			fmt.Println("message:", message.Value, "key:", message.Key, "offset:", message.Offset)
//			k.MessageQueue <- string(message.Value)
//		}
//		partitionConsumer.Close()
//	}
//}
//

