#ifndef MOTIONCOMMANDADAPTER_H
#define MOTIONCOMMANDADAPTER_H

#include <QObject>
#include "IMotionCommandObserver.h"
#include <vector>

class CMotionCommandAdapter: public QObject
{
  Q_OBJECT

public:
  CMotionCommandAdapter();
  void RegisterMotionCommandObserver(IMotionCommandObserver& aMotionCommandObserver);


public slots:
  void sltOnDbusCommandSignal(QString aCommandString);

private:
  typedef std::vector<IMotionCommandObserver*> TMotionsCommandObservers;
  TMotionsCommandObservers mMotionsCommandObservers;
  void NotifyMotionsCommandObservers();
  QString mMotionCommand;
};

#endif // MOTIONCOMMANDADAPTER_H
