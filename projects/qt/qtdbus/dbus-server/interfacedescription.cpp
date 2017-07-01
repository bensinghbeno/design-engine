#include "interfacedescription.h"
#include "ifadapter.h"

interfacedescription::interfacedescription() {


 new ifadapter(this); // Cleans itself up


 QDBusConnection dbus = QDBusConnection::sessionBus(); // Use session bus


 dbus.registerObject("/interfacedescription",this); // Register object on the bus


 dbus.registerService("com.dbus.example.interface"); // Expose interface to others


}


QString interfacedescription::read() {


 qDebug() << "Request to read was received!";


 emit somethingHappened("Emitting DBus Signal Now!");


 return QString("Request to read was received!");


}


QString interfacedescription::write() {


 qDebug() << "Request to write was received!";


 emit somethingHappened("Emitting DBus Signal Now!");


 return QString("Request to write was received!");


}


QString interfacedescription::SendMessage(const QString &cmd) {


 qDebug() << "Message Received by Server!";


 emit somethingHappened("Emitting DBus Signal Now!");


 return QString("Echoing message received: %1").arg(cmd);


}



