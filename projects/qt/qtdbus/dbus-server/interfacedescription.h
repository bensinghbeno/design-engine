#ifndef INTERFACEDESCRIPTION_H
#define INTERFACEDESCRIPTION_H

#include <QObject>

class interfacedescription:public QObject
{
  Q_OBJECT

public:
  interfacedescription();
public slots:

   QString read();

   QString write();

   QString SendMessage(const QString &cmd);

Q_SIGNALS:

   void somethingHappened(const QString &signalMessage);
};

#endif // INTERFACEDESCRIPTION_H
