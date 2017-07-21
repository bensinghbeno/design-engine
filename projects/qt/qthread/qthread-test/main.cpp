#include <iostream>
using namespace std;
#include <QThread>
#include <QtCore>
#include <QDebug>
#include <QMutex>

namespace WorkerClass
{
  static QMutex sQMutexObj;
}

class MyWorkerClass:public QThread
{
public:  
  MyWorkerClass(char* aSharedData)
    : mSharedData(aSharedData)
    , mIsSet(false)
  {}
  void run()
  {
    qDebug() << "Worker Thread Tid = " << QThread::currentThreadId() << "mSharedData = " << mSharedData;
    while(1)
    {
      if (mIsSet)
      {
        qDebug() << "Worker Thread Tid = " << QThread::currentThreadId() << "mSharedData = " << mSharedData;
        mIsSet = false;
      }
    }
  }
  char* mSharedData;
  bool  mIsSet;
};


int main(int argc, char* argv[])
{
  QCoreApplication myCoreApp(argc, argv);

  char* sharedData = new char[10];
  strcpy(sharedData,"DATA");

  MyWorkerClass myThreadObj(sharedData);
  myThreadObj.start();


  strcpy(sharedData,"DATA2");
  myThreadObj.mIsSet = true;

//  MyWorkerClass myThreadObj2;
//  myThreadObj2.setmpCString(str);
//  myThreadObj2.start();


  //qDebug() << "Main Thread Id = " << QThread::currentThreadId();

  //QObject::connect(&myThreadObj,SIGNAL(finished()),&myCoreApp,SLOT(quit()));


  return (myCoreApp.exec());
}
