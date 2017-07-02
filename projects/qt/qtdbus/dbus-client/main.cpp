#include <QCoreApplication>
#include <QObject>
#include <QDebug>
#include <QString>
#include "clientIf.h"
#include "MotionCommandAdapter.h"
#include "MotionCommandController.h"

int main(int argc, char *argv[])
{
  QCoreApplication a(argc, argv);

  clientIf* client = new clientIf("com.dbus.example.interface", "/interfacedescription", QDBusConnection::sessionBus(), 0);

  qDebug() << "Calling sendCommand() on Dbus to server...";

  CMotionCommandAdapter*     pMotionCommandAdapter    = new CMotionCommandAdapter();
  CMotionCommandController*  pMotionCommandController = new CMotionCommandController();

  if ( (pMotionCommandController!= NULL) && (pMotionCommandAdapter != NULL))
  {
    pMotionCommandAdapter->RegisterMotionCommandObserver(*pMotionCommandController);
  }

  if ( (pMotionCommandAdapter != NULL) && (client != NULL) )
  {
    QObject::connect(client,                SIGNAL(BroadcastCommandSignal(QString)),
                     pMotionCommandAdapter, SLOT(sltOnDbusCommandSignal(QString)));
  }


  client->RequestBroadcastSignal(QString("CMD_SIGNAL"));

  return a.exec();
}
