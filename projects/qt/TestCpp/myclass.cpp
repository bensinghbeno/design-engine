#include"myclass.h"
using namespace std;

MyClass::MyClass()
{
    cout<<"MyClass Constructor"<<endl;
}

MyClass::MyClass(const MyClass &rhs)
{
    std::cout<<"Copy Const"<<std::endl;
    a =  rhs.a;
}

MyClass& MyClass::operator =(const MyClass& rhs)
{
    std::cout<<"Operator = "<<std::endl;
    a = rhs.a;
}
