#include <QApplication>
#include "perceptronwidget.h"
#include "perceptronmainwindow.h"

#include <QDebug>
#include "jsonhelper.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

//    PerceptronMainWindow* pPerceptronMainWindow = new PerceptronMainWindow();

//    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();

//    pPerceptronMainWindow->addPerceptronWidget(*myPerceptronWidget);

//    pPerceptronMainWindow->show();



    JsonLoad jsonloadobj;
    jsonloadobj.demo();




    return a.exec();
}
