#ifndef DERIVED_H
#define DERIVED_H

#include "base.h"

class Derived
{
public:
    Derived();
};

class Circle:public Shape
{
public:
    Circle();
    virtual ~Circle();
    void draw();
    void setRadius(unsigned int radius);
private:
    unsigned int _radius;
};

#endif // DERIVED_H
