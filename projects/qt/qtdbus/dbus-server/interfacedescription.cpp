#include "interfacedescription.h"
#include "ifadapter.h"
#include <QTimer>
#include <QString>

interfacedescription::interfacedescription()
  : mTime(0)
  , mBroadcastSignalTimer (new QTimer(this))
{
  new ifadapter(this); // Cleans itself up
  QDBusConnection dbus = QDBusConnection::sessionBus(); // Use session bus
  dbus.registerObject("/interfacedescription",this); // Register object on the bus
  dbus.registerService("com.dbus.example.interface"); // Expose interface to others

  QObject::connect(mBroadcastSignalTimer, SIGNAL(timeout()),
                   this ,                 SLOT(SendBroadcastSignal()) );

  mBroadcastSignalTimer->start(2000);
}


void interfacedescription::sendCommand(const QString& aCommand)
{
  qDebug() << "dbus-server::sendCommand - Received Command = " << aCommand;
}

void interfacedescription::RequestBroadcastSignal(const QString& aMessage)
{
  qDebug() << "dbus-server::RequestBroadcastSignal , aMessage= " << aMessage;

  emit BroadcastCommandSignal(aMessage);
}

void interfacedescription::SendBroadcastSignal()
{
  ++mTime;
  QString sigMessage = QString::number(mTime) + " SECONDS BROADCASTED !! ";

  qDebug() << "dbus-server::SendBroadcastSignal to clients , aMessage= " << sigMessage;

  emit BroadcastCommandSignal(sigMessage);
}





