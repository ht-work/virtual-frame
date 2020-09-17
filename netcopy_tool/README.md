##usage
```sh
ncp-server [-h] [-i [IP]] [-p PORT] [-v]
ncp-client [-h] [-o {get,put}] [-i IP] [-p PORT] [-l LOCALFILE] [-r REMOTEFILE] [-e] [-v]
```

##optional arguments
```sh
ncp-server
optional arguments:
  -h, --help            show this help message and exit
  -i [IP], --ip [IP]    server's ip
  -p PORT, --port PORT  server's port
  -v, --verbose         enable debug message

ncp-client
optional arguments:
  -h, --help            show this help message and exit
  -o {get,put}, --operation {get,put}
                        run as client
  -i IP, --ip IP        server's ip
  -p PORT, --port PORT  server's port
  -l LOCALFILE, --localfile LOCALFILE
                        path of local file
  -r REMOTEFILE, --remotefile REMOTEFILE
                        path of remote file
  -v, --verbose         enable debug message
```

##example
```sh
ncp-server -i 127.0.0.1 -p 12345
ncp-client -o put -l /data/images/netcp_test.img -r /tmp/netcp_test.img -i 127.0.0.1 -p 12345
```
