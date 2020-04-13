# SomeIp for Dummies

> If you are here then you probably could not get the page to work :D.

# Lets get started!

Build & install the git-repos as follows,

mkdir build && cd build/ && cmake .. && make $(nproc) && sudo make install

For the below repos use maven build (xtend version patch already applied),

Core tools

$ cd capicxx-core-tools
$ cd org.genivi.commonapi.core.releng
$ mvn -Dtarget.id=org.genivi.commonapi.core.target clean verify
$ mkdir -p /opt/commonapi-generator/
$ chown <user> /opt/commonapi-generator/
$ unzip ../org.genivi.commonapi.core.cli.product/target/products/commonapi-generator.zip -d  /opt/commonapi-generator/
$ chmod +x /opt/commonapi-generator/commonapi-generator-linux-x86_64
$ ln -s /opt/commonapi-generator/commonapi-generator-linux-x86_64 /usr/bin/capicxx-core-gen

Someip-tools

$ cd capicxx-someip-tools
$ cd org.genivi.commonapi.someip.releng
$ mvn -DCOREPATH=<absolute-path-to-capicxx-core-tools> -Dtarget.id=org.genivi.commonapi.someip.target clean verify
$ mkdir -p /opt/commonapi-someip-generator/
$ chown <user> /opt/commonapi-someip-generator/
$ unzip ../org.genivi.commonapi.someip.cli.product/target/products/commonapi_someip_generator.zip -d /opt/commonapi-someip-generator/
$ chmod +x /opt/commonapi-someip-generator/commonapi-someip-generator-linux-x86_64
$ ln -s /opt/commonapi-someip-generator/commonapi-someip-generator-linux-x86_64 /usr/bin/capicxx-someip-gen


Generate code: 

cd example/
rm -rf src-gen
capicxx-core-gen -sk ./fidl/HelloWorld.fidl
capicxx-someip-gen -ll verbose ./fidl/HelloWorld.fdepl

Build the example:

mkdir build && cd build/ && cmake .. && make $(nproc)

Add route:

sudo route add -nv 224.244.224.245 dev eth0

Setup & Start daemon:

sudo cp config/vsomeip.json /etc/vsomeip/

vsomeipd

log :: 

ben@ben-ubuntu18:~/devel/someip/example/build$ vsomeipd 
[ 4642.135946]~DLT~ 3422~INFO     ~FIFO /tmp/dlt cannot be opened. Retrying later...
2020-04-13 18:22:48.646919 [error] Multiple applications are configured to use client identifier 1277. Ignoring the configuration for application MultiFunctionalSeatsServer
2020-04-13 18:22:48.647123 [info] Parsed vsomeip configuration in 0ms
2020-04-13 18:22:48.647157 [info] Using configuration folder: "/etc/vsomeip".
2020-04-13 18:22:48.647167 [info] Default configuration module loaded.
2020-04-13 18:22:48.647172 [info] Initializing vsomeip application "vsomeipd".
2020-04-13 18:22:48.647227 [info] SOME/IP client identifier configured. Using 0001 (was: 0000) and UID/GID=1000/1000
2020-04-13 18:22:48.647241 [info] Instantiating routing manager [Host].
2020-04-13 18:22:48.647291 [info] init_routing_endpoint Routing endpoint at /tmp/vsomeip-0
2020-04-13 18:22:48.647376 [info] Client [1] is connecting to [0] at /tmp/vsomeip-0
2020-04-13 18:22:48.647397 [info] Service Discovery enabled. Trying to load module.
2020-04-13 18:22:48.647581 [info] Service Discovery module loaded.
2020-04-13 18:22:48.647619 [info] vsomeip tracing not enabled. . vsomeip service discovery tracing not enabled. 
2020-04-13 18:22:48.647626 [info] Application(vsomeipd, 0001) is initialized (11, 100).
2020-04-13 18:22:48.647636 [info] Starting vsomeip application "vsomeipd" (0001) using 2 threads I/O nice 255
2020-04-13 18:22:48.647726 [info] main dispatch thread id from application: 0001 (vsomeipd) is: 7f676b051700 TID: 3426
2020-04-13 18:22:48.647761 [info] Watchdog is disabled!
2020-04-13 18:22:48.647759 [info] shutdown thread id from application: 0001 (vsomeipd) is: 7f676a850700 TID: 3427
2020-04-13 18:22:48.647817 [info] io thread id from application: 0001 (vsomeipd) is: 7f676fd9d800 TID: 3422
2020-04-13 18:22:48.647839 [info] io thread id from application: 0001 (vsomeipd) is: 7f676984e700 TID: 3429
2020-04-13 18:22:48.647870 [info] vSomeIP 2.14.16 | (default)
2020-04-13 18:22:48.647881 [info] Sent READY to systemd watchdog
2020-04-13 18:22:48.647917 [info] Network interface "enp0s3" state changed: up
2020-04-13 18:22:48.647973 [info] Route "224.244.224.245/32 if: enp0s3 gw: n/a" state changed: up
2020-04-13 18:22:48.648001 [info] udp_server_endpoint_impl: SO_RCVBUF is: 212992
2020-04-13 18:22:48.648439 [info] SOME/IP routing ready.

Start example server:

x@ubuntu:~/work/project/build$ VSOMEIP_APPLICATION_NAME=service-sample ./HelloWorldService &
[1] 5049
x@ubuntu:~/work/project/build$ 2015-09-18 01:54:25.924662 [info] Using configuration file: ../fidl/vsomeip.json
2015-09-18 01:54:25.928805 [debug] Routing endpoint at /tmp/vsomeip-0
2015-09-18 01:54:25.929315 [info] Service Discovery disabled. Using static routing information.
2015-09-18 01:54:25.929443 [debug] Application(service-sample, 1277) is initialized (uses 0 dispatcher threads).
Successfully Registered Service! Waiting for calls... (Abort with CTRL+C)

Start Client:

x@ubuntu:~/work/project/build$ VSOMEIP_APPLICATION_NAME=client-sample ./HelloWorldClient
2015-09-18 01:58:42.382432 [info] Using configuration file: ../fidl/vsomeip.json
2015-09-18 01:58:42.382750 [debug] Connecting to [0] at /tmp/vsomeip-0
2015-09-18 01:58:42.382969 [debug] Listening at /tmp/vsomeip-1343
2015-09-18 01:58:42.383024 [debug] Application(client-sample, 1343) is initialized (uses 0 dispatcher threads).
Checking availability!
2015-09-18 01:58:42.383918 [debug] Application/Client 1343 got registered!
Available...
sayHello('Bob'): 'Hello Bob!'
Got message: 'Hello Bob!'
2015-09-18 01:58:42.385127 [debug] Application/Client 1343 got deregistered!
2015-09-18 01:58:42.385230 [error] Local endpoint received message (Operation canceled)



Ta daa!! :D ....





