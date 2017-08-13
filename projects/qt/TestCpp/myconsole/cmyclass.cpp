#include "cmyclass.h"
#include "utils.h"
#include <iostream>
using namespace std;

CMyClass::CMyClass()
{
  cout << "CMyClass::CMyClass()" << endl;
}

void CMyClass::processInput(int aArgc, char** aArgv)
{
  MY_UNUSED(aArgc);
  MY_UNUSED(aArgv);
  cout << "CMyClass::processInput()" << endl;
}

