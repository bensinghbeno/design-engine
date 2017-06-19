#include <iostream>
using namespace std;
#include <QtCore>

class Base
{
public:
  Base(){}
  virtual ~Base(){}
  void call()
  {
    cout<<"Base"<<endl;
  }

};

class IBase
{
public:
  virtual ~IBase(){}
  virtual void call() = 0;
};

class Child : public IBase
{
public:
  Child():val(0){}
  virtual ~Child(){}
  void call()
  {
    cout<<"val = "<<val<<endl;
  }
  quint32 val;
  void setval(quint32 aval)
  {
    val = aval;
  }
};

class Other
{
public:
  IBase* bp;
  void set(IBase* abp)
  {
    bp = abp;
  }
  void call()
  {
    bp->call();
  }
};


int main(int argc, char **argv)
{
  cout<<"Hello MyConsole!!"<<endl;
  Child* cp = new Child;
  const quint32 v = 10;
  cp->setval(v);
  Other otherObj;
  otherObj.set(cp);
  otherObj.call();
}
