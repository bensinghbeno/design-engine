#include"dbusinterface.h"
#include "utils.h"
#include "pthread.h"

void task_listen_dbus_message(void* _thread_arg)
{
    printf("thread - task_listen_dbus_message started\n");
    worker_thread_args  thread_arg = *((worker_thread_args*) _thread_arg);
    DBusConnection* dbusConnection = thread_arg.dbusConnection;

    while (true)
    {
        // Acquire R/W access to Bus
        dbus_connection_read_write(dbusConnection, 0);
        DBusMessage* dbusMsg = dbus_connection_pop_message(dbusConnection);

        if (NULL == dbusMsg)
        {
            sleep(1);
            continue;
        }

        if ( dbus_message_has_interface(dbusMsg, thread_arg.interface) )
        {
            listen_to_method_requests( dbusMsg, thread_arg.interface, dbusConnection );
        }
        // Unref the message
        dbus_message_unref(dbusMsg);
    }
}

int main(int argc,char* argv[])
{
    printf("Launched DBusServer Application\n");


    if(check_server_arguments(argc,argv))
    {

        printf("DBusServer Application server arguments validated\n");

        add_callback("ACTION_0",&action_function_get_year);
        callback_vector_display_values();


        DBusError dbusErrorStructure;
        DBusConnection* dbusConnection;
        int resultBusNameReg;

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

        printf("Start Main DBus Server Loop as a worker thread to listen & respond to messages\n");


        pthread_t thread;
        pthread_attr_t attr;
        int rc;
        long t=0;
        void *status;
        worker_thread_args thread_arg;
        thread_arg.task_id = t;
        thread_arg.interface = argv[2];
        thread_arg.dbusConnection = dbusConnection;


        /* Initialize and set thread detached attribute */
        pthread_attr_init(&attr);
        pthread_attr_setdetachstate(&attr, PTHREAD_CREATE_JOINABLE);

        printf("Main: creating thread %ld\n", t);
        rc = pthread_create(&thread, &attr, (void*)&task_listen_dbus_message, (void *)(&thread_arg));
        if (rc) {
            printf("ERROR; return code from pthread_create() is %d\n", rc);
            exit(-1);
        }

        pthread_attr_destroy(&attr);
        rc = pthread_join(thread, &status);
        if (rc) {
            printf("ERROR; return code from pthread_join() is %d\n", rc);
            exit(-1);
        }
        printf("Main Thread: completed join with thread %ld having a status of %ld\n",t,(long)status);

    }
    else
    {
        return RET_ERROR;
    }
}
