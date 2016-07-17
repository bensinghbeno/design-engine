#include"dbusinterface.h"

int main(int argc, char **argv)
{
    DBusMessage* dbusMsg;
    DBusMessageIter args;
    DBusConnection* dbusConnection;
    DBusError dbusErrorStructure;
    DBusPendingCall* dbusPendingCall;
    int resultBusNameReg;
    int responseYear;
    int request_id = REQUEST_ID;
    int command_id = COMMAND_ID;


    if (check_client_arguments(argc,argv))
    {
        printf("DBus Client Launched\n");

        printf("Call DBus method with %d %d\n",request_id,command_id);

        // init the dbus error structure
        dbus_error_init(&dbusErrorStructure);

        // Try to connecte with the dbus daemon
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

        // request our name on the bus
        resultBusNameReg = dbus_bus_request_name(dbusConnection, "org.dbusclient.methodrequestor", DBUS_NAME_FLAG_REPLACE_EXISTING , &dbusErrorStructure);
        if (dbus_error_is_set(&dbusErrorStructure))
        {
            fprintf(stderr, "ERROR in Bus name request = (%s)\n , result = %d", dbusErrorStructure.message,resultBusNameReg);
            dbus_error_free(&dbusErrorStructure);
        }

        // New method creation
        dbusMsg = dbus_message_new_method_call(argv[1],argv[2],argv[3],"Method");
        if (NULL == dbusMsg)
        {
            fprintf(stderr, "ERROR:: The Message is Null\n");
            exit(1);
        }
        else
        {
            printf("SUCCESS:: Message is created\n");
        }

        // Add RequestID & Command to the message as payload
        dbus_message_iter_init_append(dbusMsg, &args);
        if (!dbus_message_iter_append_basic(&args, DBUS_TYPE_INT32, &request_id))
        {
            fprintf(stderr, "ERROR :: Memory Unavailable\n");
            exit(1);
        }

        if (!dbus_message_iter_append_basic(&args, DBUS_TYPE_INT32, &command_id))
        {
            fprintf(stderr, "ERROR :: Memory Unavailable\n");
            exit(1);
        }

        // Sending the Message with an expected response
        if (!dbus_connection_send_with_reply (dbusConnection, dbusMsg, &dbusPendingCall, -1))
        {
            fprintf(stderr, "ERROR :: Memory Unavailable\n");
            exit(1);
        }
        if (NULL == dbusPendingCall)

        {
            fprintf(stderr, "Pending Call Null\n");
            exit(1);
        }
        dbus_connection_flush(dbusConnection);

        printf("SUCCESS:: Message Request Sent\n");

        // Unref the message
        dbus_message_unref(dbusMsg);

        // Blocking call to await a response
        dbus_pending_call_block(dbusPendingCall);

        // Process the Reply message
        dbusMsg = dbus_pending_call_steal_reply(dbusPendingCall);
        if (NULL == dbusMsg)
        {
            fprintf(stderr, "Response is Null\n");
            exit(1);
        }
        dbus_pending_call_unref(dbusPendingCall);

        // Read the message parameters
        if (!dbus_message_iter_init(dbusMsg, &args))
        {
            fprintf(stderr, "The Message is without arguments!\n");
        }
        else
        {
            dbus_message_iter_get_basic(&args, &responseYear);
        }

        printf("Received the Response, Current Year = %d\n",responseYear);

        // Unref the connection. Do not close as it's a shared connection.
        dbus_message_unref(dbusMsg);
        return 0;

    }
    else
    {
        return RET_ERROR;
    }
}
