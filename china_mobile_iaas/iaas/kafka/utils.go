package kafka

import "crypto/tls"

func genTLSConfig(clientcert string, clientkey string, cacert string) (*tls.Config, error) {
	//cert, err := tls.LoadX509KeyPair(clientcert, clientkey)
	//if err != nil {
	//	fmt.Println("tls cert err:", err)
	//}
	//
	//cacert, err = ioutil.ReadFile(cacert)
	//if err != nil {
	//	fmt.Print("failed open cert file.", err)
	//}
	//cacertpool := x509.NewCertPool()
	//cacertpool.AppendCertsFromPEM(cacert)
	//
	//tlsConfig := tls.Config{}
	//tlsConfig.RootCAs = cacertpool
	//tlsConfig.Certificates = []tls.Certificate{cert}
	//tlsConfig.BuildNameToCertificate()
	return nil, nil
}