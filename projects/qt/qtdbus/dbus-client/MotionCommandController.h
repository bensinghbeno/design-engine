#ifndef MOTIONCOMMANDCONTROLLER_H
#define MOTIONCOMMANDCONTROLLER_H

#include "IMotionCommandObserver.h"

class CMotionCommandController:public IMotionCommandObserver
{
public:
  CMotionCommandController();
  /**
   * @brief onMotionCommand callback from IMotionCommandObserver interface
   * @param aCommand string
   */
  void onMotionCommand(const QString& aCommand);

};

#endif // MOTIONCOMMANDCONTROLLER_H
