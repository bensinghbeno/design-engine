#include <QCoreApplication>
#include <QObject>
#include <QDebug>
#include "clientIf.h"

int main(int argc, char *argv[])
{
  QCoreApplication a(argc, argv);

  clientIf* client = new clientIf("com.dbus.example.interface", "/interfacedescription", QDBusConnection::sessionBus(), 0);


  // Define a signal receiver and hook up it's slot to the Dbus generated signal

  SignalReceiver rx;

  QObject::connect(client,SIGNAL(somethingHappened(QString)), &rx, SLOT(receivedSignal(QString)));


  qDebug() << "Sending Read() command over Dbus to server...";

  client->read();

  qDebug() << "Done sending read command...";


  qDebug() << "Sending Write() command over Dbus to server...";

  client->write();

  qDebug() << "Done sending write command...";


  QString messageToSend("Hello World!");

  client->SendMessage(messageToSend);




  return a.exec();
}
