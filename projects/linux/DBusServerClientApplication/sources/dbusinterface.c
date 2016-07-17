#include "dbusinterface.h"

const int RET_ERROR = -1;
const int MIN_OCTETS = 3;
const int REQUEST_ID = 1001;
const int COMMAND_ID = 111;

bool validate_name_octets(char* name, char key)
{
    int octets = 0;
    int c = 0;
    char string[30];
    strcpy(string,name);

    while (string[c] != '\0')
    {
        if(string[c] == key)
        {
            ++octets;
        }
        c++;
    }

    if((++octets) < MIN_OCTETS)
    {
        return false;
    }

    return true;
}


bool check_client_arguments(int argc, char* argv[])
{
    if(argc == 4)
    {
        if(validate_name_octets(argv[1],'.') && validate_name_octets(argv[2],'/') && validate_name_octets(argv[3],'.'))
        {
            printf("Server-Busname = %s, Object Name = %s, Interface Name = %s\n",argv[1],argv[2],argv[3]);
            return true;
        }
        else
        {

            printf("Server-Busname = %s, Object Name = %s, Interface Name = %s\n ERROR:: Short octets found in names, Please provide atleast 3 octets in Bus Method & Interface Names\n", argv[1],argv[2],argv[3]);
            printf("Please launch like :: ./clientdbusapplication.out server-busname objectname ifacename\n E.g. ./clientdbusapplication.out org.bus.server /org/method/object org.method.iface \n");

            return false;
        }
    }
    else
    {
        printf("ERROR:: Invalid commandline arguments\n Please launch like :: ./clientdbusapplication.out server-busname objectname ifacename\n E.g:: ./clientdbusapplication.out org.bus.server /org/method/object org.method.iface \n");
        return false;
    }

}

bool check_server_arguments(int argc, char* argv[])
{
    if(argc == 3)
    {
        if(validate_name_octets(argv[1],'.') && validate_name_octets(argv[2],'.'))
        {
            printf("Bus Name = %s, Iface name = %s\n", argv[1],argv[2]);
            return true;
        }
        else
        {
            printf("Bus Name = %s, Iface name = %s\n ERROR:: Short octets found in names, Please provide atleast 3 octets in Bus & Interface Names\n", argv[1],argv[2]);
            printf("Please launch like :: ./serverdbusapplication.out busname ifacename\n E.g:: ./serverdbusapplication.out org.bus.server org.method.iface \n");
            return false;
        }
    }
    else
    {
        printf("ERROR:: Invalid commandline arguments\n Please launch like :: ./serverdbusapplication.out busname ifacename\n E.g. ./serverdbusapplication.out org.bus.server org.method.iface \n");
        return false;
    }

}

int register_bus_name(char* busName, DBusConnection *dbusConnection, DBusError* dbusErrorStructure)
{
    int result = dbus_bus_request_name(dbusConnection,busName, DBUS_NAME_FLAG_REPLACE_EXISTING , dbusErrorStructure);
    if (dbus_error_is_set(dbusErrorStructure))
    {
        fprintf(stderr, "Bus Name Registration Error (%s)\n", dbusErrorStructure->message);
        dbus_error_free(dbusErrorStructure);
    }
    else
    {
        printf("SUCCESS:: Bus Name Registered\n");
    }

    return result;
}

void listen_to_method_requests(DBusMessage* msg, const char* iface, DBusConnection* conn)
{
    DBusMessage* messageReply;
    dbus_uint32_t requestID;
    dbus_uint32_t requestCommand;
    dbus_uint32_t response;
    DBusMessageIter dbusMsgIter;


    // read the arguments
    if (!dbus_message_iter_init(msg,&dbusMsgIter))
    {
        fprintf(stderr, "Method has no arguments!\n");
    }

    //Get Dbus Iterator
    dbus_message_iter_get_basic(&dbusMsgIter, &requestID);

    printf("SUCCESS:: Request ID  = %d\n", requestID);
    if(dbus_message_iter_has_next(&dbusMsgIter))
    {
        dbus_message_iter_next(&dbusMsgIter);
        dbus_message_iter_get_basic(&dbusMsgIter, &requestCommand);
        printf("SUCCESS:: Command = %d\n", requestCommand);
    }

    if ( dbus_message_is_method_call( msg, iface, "Method" ) )
    {
        if(requestID == 1001)
        {
            time_t now = time(NULL);
            struct tm *t = localtime(&now);
            response = t->tm_year+1900;
            printf( "The Year is %d\n", response);
        }
        else
        {
            printf( "ERROR:: Invalid request ID");
        }
    }
    // Respond to the method request
    messageReply = dbus_message_new_method_return(msg);
    dbus_message_iter_init_append(messageReply, &dbusMsgIter);

    if (!dbus_message_iter_append_basic(&dbusMsgIter, DBUS_TYPE_INT32, &response))
    {
        fprintf(stderr, "ERROR :: Memory Unavailable\n");
        exit(1);
    }

    // Respond and Clear the connection
    if (!dbus_connection_send(conn, messageReply, &response)) {
        fprintf(stderr, "ERROR :: Memory Unavailable\n");
        exit(1);
    }

    dbus_connection_flush(conn);
    dbus_message_unref(messageReply);
}
