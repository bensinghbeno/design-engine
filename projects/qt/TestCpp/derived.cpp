#include "derived.h"
#include "utils.h"
using namespace std;

Derived::Derived()
{

}

Circle::Circle():_radius(ZERO)
{
    cout<<"Circle::Circle()"<<endl;
}

Circle::~Circle()
{
    cout<<"Circle::~Circle()"<<endl;
}

void Circle::setRadius(unsigned int radius)
{
    _radius = radius;
}


void Circle::draw()
{
    if(_radius != ZERO )
    {
        cout<<"radius   = "<<_radius<<endl;
        cout<<"Circle::draw(): Success";
    }
    else
    {
        cout<<"Circle::draw(): Please set radius"<<endl;
    }
}
