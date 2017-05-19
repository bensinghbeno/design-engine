#include <boost/optional.hpp>
#include <boost/foreach.hpp>
#include <iostream>
using namespace std;
#include <QtCore>


struct mystruct
{
  char str[10];
  qint32 val;
};


int main(int argc, char *argv[])
{
  cout<<"Qt Console"<<endl;

  char* p;
  int* ip;

  mystruct mystruc;


  strcpy(mystruc.str,"hello");
  mystruc.val = 100;


  cout<<"val = "<<mystruc.val<<endl;
  cout<<"str = "<<mystruc.str<<endl;

  return 0;
}
