/* file  : main.cpp for qt console test app
 * author: bensinghbeno
*/

#include "cmyclass.h"
#include <iostream>
using namespace std;

class net
{
public:

  net(){}

private:

};

int main(int argc, char* argv[])
{
    #if __cplusplus==201402L
    std::cout << "C++14" << std::endl;
    #elif __cplusplus==201103L
    std::cout << "C++11" << std::endl;
    #else
    std::cout << "C++" << std::endl;
    #endif

  CMyClass* pCMyClass = new CMyClass;
  pCMyClass->processInput(argc, argv);
  delete pCMyClass;

  return 0;
}
