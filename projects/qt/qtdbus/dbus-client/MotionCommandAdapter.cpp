#include "MotionCommandAdapter.h"
#include <QtDebug>


CMotionCommandAdapter::CMotionCommandAdapter()
{

}

void CMotionCommandAdapter::RegisterMotionCommandObserver(IMotionCommandObserver& aMotionCommandObserver)
{
  mMotionsCommandObservers.push_back(&aMotionCommandObserver);
}

void CMotionCommandAdapter::NotifyMotionsCommandObservers()
{
  qDebug() << "mMotionsCommandObservers =  " << mMotionsCommandObservers.size();
  for(TMotionsCommandObservers::iterator it = mMotionsCommandObservers.begin();
      it != mMotionsCommandObservers.end();
      ++it)
  {
    (*it)->onMotionCommand(mMotionCommand);
  }

}


void CMotionCommandAdapter::sltOnDbusCommandSignal(QString aCommandString)
{
  qDebug() << "CMotionCommandAdapter::sltOnDbusCommandSignal = " << aCommandString;
  mMotionCommand = aCommandString;
  NotifyMotionsCommandObservers();
}

