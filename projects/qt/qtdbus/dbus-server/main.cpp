#include <QCoreApplication>
#include <QDebug>
#include "interfacedescription.h"

int main(int argc, char *argv[])
{
  QCoreApplication a(argc, argv);

  qDebug() << "Initializing DBus Server...";

  qDebug() << "Creating interface...";


  // Create a dbus instance

  new interfacedescription();


  qDebug() << "Done creating interface...";

  qDebug() << "Waiting for messages...";

  return a.exec();
}
