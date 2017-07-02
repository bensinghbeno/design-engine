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

  void setmpCString(const QString& aQString)
  {
    WorkerClass::sQMutexObj.lock();
    mSharedQString = aQString;
    WorkerClass::sQMutexObj.unlock();
  }
  const QString& getmpCString() const
  {
    return mSharedQString;
  }

  void run()
  {
    qDebug() << "Worker Thread Tid = " << QThread::currentThreadId() << "mSharedQString = " << getmpCString();
    while(1)
    {}
  }
private:
  QString mSharedQString;
};


int main(int argc, char* argv[])
{
  QCoreApplication myCoreApp(argc, argv);

  const QString& str = *(new QString("SHARED_QSTRING"));

  MyWorkerClass myThreadObj;
  myThreadObj.setmpCString(str);
  myThreadObj.start();

  MyWorkerClass myThreadObj2;
  myThreadObj2.setmpCString(str);
  myThreadObj2.start();


  qDebug() << "Main Thread Id = " << QThread::currentThreadId();

  //QObject::connect(&myThreadObj,SIGNAL(finished()),&myCoreApp,SLOT(quit()));


  return (myCoreApp.exec());

}
