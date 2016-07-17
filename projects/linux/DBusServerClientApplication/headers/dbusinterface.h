#ifndef DBUSINTERFACE_H
#define DBUSINTERFACE_H


#include <stdbool.h>
#include <stdlib.h>
#include <dbus/dbus-glib.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <dbus-1.0/dbus/dbus.h>
#include <math.h>

const int RET_ERROR;
const int MIN_OCTETS;
const int REQUEST_ID;
const int COMMAND_ID;


// This function initiates listening for method calls for a dbus server
void listen_to_method_requests(DBusMessage* msg, const char* iface, DBusConnection* conn);

// This function can Request & Register for a Name on DBus with a valid error structure
int register_bus_name(char* busName, DBusConnection* dbusConnection, DBusError* dbusErrorStructure);

// This is a helper function to validate command line arguments for the server-application during launch via terminal
bool check_server_arguments(int argc, char* argv[]);

// This is a helper function to validate command line arguments for the server-application during launch via terminal
bool check_client_arguments(int argc, char* argv[]);

// This is a helper function to validate the minimal number of octets to be provided in Bus,Interface & method Names
bool validate_name_octets(char* name, char key);



#endif // DBUSINTERFACE_H
