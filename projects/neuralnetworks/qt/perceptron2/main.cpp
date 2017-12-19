#include <QApplication>
#include <QDebug>

#include "perceptronwidget.h"
#include "perceptroncontroller.h"
#include "jsonhelper.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();
    PerceptronController myPerceptronController(*myPerceptronWidget);


    JsonHelper jsonHelperObj;
    jsonHelperObj.demo();


    return a.exec();
}
