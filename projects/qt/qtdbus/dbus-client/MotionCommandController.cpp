#include <QDebug>
#include "MotionCommandController.h"

CMotionCommandController::CMotionCommandController()
{

}

void CMotionCommandController::onMotionCommand(const QString& aCommand)
{
  qDebug() << "CMotionCommandController::onMotionCommand callback : " << aCommand;
}
