#include "base.h"
#include"utils.h"
using namespace std;

Base::Base()
{
}

Shape::Shape()
    :_xpos(ZERO)
    ,_ypos(ZERO)
{
    cout<<"Shape::Shape()"<<endl;
}
Shape::~Shape()
{
    cout<<"Shape::~Shape()"<<endl;
}

void Shape::setCoordinates(const unsigned int xpos, const unsigned int ypos)
{
    _xpos = xpos;
    _ypos = ypos;
}

void Shape::draw()
{
    cout<<"Shape::draw() : Success"<<endl;

}
