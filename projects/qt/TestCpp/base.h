#ifndef BASE_H
#define BASE_H


class Base
{
public:
    Base();
};

class Shape
{
public:
    Shape();
    virtual ~Shape();
    virtual void setCoordinates(unsigned const int xpos, unsigned const int ypos);
    virtual void draw();

private:
    unsigned int _xpos;
    unsigned int _ypos;
};


#endif // BASE_H
