#include "interfacedescription.h"
#include "ifadapter.h"

interfacedescription::interfacedescription()
{
  new ifadapter(this); // Cleans itself up
  QDBusConnection dbus = QDBusConnection::sessionBus(); // Use session bus
  dbus.registerObject("/interfacedescription",this); // Register object on the bus
  dbus.registerService("com.dbus.example.interface"); // Expose interface to others
}


QString interfacedescription::sendCommand(const QString& aCommand)
{
  qDebug() << "dbus-server::sendCommand - Received Command = " << aCommand;
}



