#include <QCoreApplication>
#include <QObject>
#include <QDebug>
#include "clientIf.h"

int main(int argc, char *argv[])
{
  QCoreApplication a(argc, argv);

  clientIf* client = new clientIf("com.dbus.example.interface", "/interfacedescription", QDBusConnection::sessionBus(), 0);

  qDebug() << "Calling sendCommand() on Dbus to server...";

  client->sendCommand("CMD_START");

  return a.exec();
}
