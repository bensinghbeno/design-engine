/* file  : main.cpp for qt console test app
 * author: bensinghbeno
*/

#include "cmyclass.h"
#include <iostream>
using namespace std;

int main(int argc, char* argv[])
{

  cout << "Hello myconsole tesapp" << endl;

  CMyClass* pCMyClass = new CMyClass;
  pCMyClass->processInput(argc, argv);
  delete pCMyClass;

  return 0;
}
