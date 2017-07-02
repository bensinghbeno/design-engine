#ifndef INTERFACEDESCRIPTION_H
#define INTERFACEDESCRIPTION_H

#include <QObject>
#include <QTimer>

class interfacedescription:public QObject
{
  Q_OBJECT

public:
  interfacedescription();

public slots:
   void sendCommand(const QString& aCommand);
   void RequestBroadcastSignal(const QString& aMessage);
   void SendBroadcastSignal();

Q_SIGNALS:
   void BroadcastCommandSignal(const QString& aCommandMessage);

private:
   qint32 mTime;
   QTimer* mBroadcastSignalTimer;
};

#endif // INTERFACEDESCRIPTION_H
