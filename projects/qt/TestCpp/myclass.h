#ifndef MYCLASS_H
#define MYCLASS_H

#include "utils.h"

const int glob=55;

class MyClass
{

public:
    MyClass();
    MyClass(const MyClass& rhs);
    MyClass& operator =(const MyClass& rhs);
    int geta(){return a;}
protected:
    int a;
};



#endif // MYCLASS_H
