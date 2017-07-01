#ifndef INTERFACEDESCRIPTION_H
#define INTERFACEDESCRIPTION_H

#include <QObject>

class interfacedescription:public QObject
{
  Q_OBJECT

public:
  interfacedescription();
public slots:
   QString sendCommand(const QString& aCommand);
};

#endif // INTERFACEDESCRIPTION_H
