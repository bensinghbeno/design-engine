/* file  : main.cpp for qt console test app
 * author: bensinghbeno
*/

#include <iostream>
using namespace std;

int main(int argc, char* argv[])
{
  cout<<"Hello myconsole tesapp"<<endl;

    #if __cplusplus==201402L
    std::cout << "C++14" << std::endl;
    #elif __cplusplus==201103L
    std::cout << "C++11" << std::endl;
    #else
    std::cout << "C++" << std::endl;
    #endif


  return 0;
}
