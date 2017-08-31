/* file  : main.cpp for qt console test app
 * author: bensinghbeno
*/

#include "cmyclass.h"
#include <iostream>
using namespace std;

int main(int argc, char* argv[])
{
<<<<<<< 11882b47357fe369edffae270e1a26d89d90ab09
  cout<<"Hello myconsole tesapp"<<endl;

    #if __cplusplus==201402L
    std::cout << "C++14" << std::endl;
    #elif __cplusplus==201103L
    std::cout << "C++11" << std::endl;
    #else
    std::cout << "C++" << std::endl;
    #endif
=======

  cout << "Hello myconsole tesapp" << endl;
>>>>>>> myconsole: added myclass and corrected utils

  CMyClass* pCMyClass = new CMyClass;
  pCMyClass->processInput(argc, argv);
  delete pCMyClass;

  return 0;
}
