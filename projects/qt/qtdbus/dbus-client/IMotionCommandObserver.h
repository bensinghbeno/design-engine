/**
  * @File        : IMotionCommandObserver
  * @Description : This file declares the interface for MotionCommandObserver
  * @Author      : Bensingh Beno
*/

#ifndef  IMOTIONCOMMANOBSERVER_H
#define  IMOTIONCOMMANOBSERVER_H

class QString;

class IMotionCommandObserver
{
public:
  IMotionCommandObserver(){}
  virtual ~IMotionCommandObserver(){}
  virtual void onMotionCommand(const QString& aCommand) = 0;
};

#endif // IMOTIONCOMMANOBSERVER_H
