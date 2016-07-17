#include"dbusinterface.h"
#include <time.h>


int main(int argc,char* argv[])
{
    DBusError dbusErrorStructure;
    DBusConnection* dbusConnection;
    DBusMessage* dbusMsg;
    int resultBusNameReg;

    if(check_server_arguments(argc,argv))
    {

        printf("Launched DBusServer Application\n");

        // init the dbus error structure
        dbus_error_init(&dbusErrorStructure);


        // Try to connect with the dbus daemon
        dbusConnection = dbus_bus_get(DBUS_BUS_SESSION,&dbusErrorStructure);
        if (dbus_error_is_set(&dbusErrorStructure))
        {
            fprintf(stderr, "Error while connecting (%s)\n", dbusErrorStructure.message);
            dbus_error_free(&dbusErrorStructure);
        }

        // Check if the connection is successful
        if (NULL == dbusConnection)
        {
            fprintf(stderr, "FAILURE:: Connection is Null\n");
            exit(1);
        }
        else
        {
            printf("SUCCESS:: Connected to DBus Daemon\n");
        }

        resultBusNameReg = register_bus_name(argv[1], dbusConnection, &dbusErrorStructure);
        if(RET_ERROR == resultBusNameReg)
        {
            return resultBusNameReg;
        }

        printf("Start Main DBus Server Loop to listen & respond to messages\n");
        while (true)
        {
            // Acquire R/W access to Bus
            dbus_connection_read_write(dbusConnection, 0);
            dbusMsg = dbus_connection_pop_message(dbusConnection);

            if (NULL == dbusMsg)
            {
                sleep(1);
                continue;
            }

            if ( dbus_message_has_interface(dbusMsg, argv[2]) )
            {
                listen_to_method_requests( dbusMsg, argv[2], dbusConnection );
            }
            // Unref the message
            dbus_message_unref(dbusMsg);
        }
    }
    else
    {
        return RET_ERROR;
    }
}
