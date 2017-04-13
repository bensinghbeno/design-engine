#include <boost/optional.hpp>
#include <boost/foreach.hpp>
#include <iostream>
using namespace std;
#include <QtCore>


int main(int argc, char *argv[])
{
    cout<<"Qt Console"<<endl;


    QList<QString> sl;

    sl.push_back("1");
    sl.push_back("2");
    sl.push_back("3");


    BOOST_FOREACH(QString qstr, sl)
    {
      cout<<qstr.toStdString()<<endl;
    }



    return 0;
}
