#include <QThread>
#include <QtCore>
#include <QDebug>

class MyWorkerClass:public QThread
{
public:
  char* mpCString;
  void setmpCString(char* apCString)
  {
    mpCString = apCString;
  }

  void run()
  {
    qDebug() << "Worker Thread Tid = " << QThread::currentThreadId() << "mpCString = " << mpCString;
    while(1)
    {}
  }

};


int main(int argc, char* argv[])
{
  QCoreApplication myCoreApp(argc, argv);

  QString str("MYSTRING");
  char* mCString = new char[10];
  strncpy(mCString,str.toStdString().c_str(),(str.size()+1));

  MyWorkerClass myThreadObj;
  myThreadObj.setmpCString(mCString);
  myThreadObj.start();

  MyWorkerClass myThreadObj2;
  myThreadObj2.setmpCString(mCString);
  myThreadObj2.start();


  qDebug() << "Main Thread Id = " << QThread::currentThreadId();

  //QObject::connect(&myThreadObj,SIGNAL(finished()),&myCoreApp,SLOT(quit()));


  return (myCoreApp.exec());

}
