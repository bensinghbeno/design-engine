#include <QApplication>
#include <QDebug>

#include "perceptronwidget.h"
#include "jsonhelper.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

//    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();
//    myPerceptronWidget->createMasterLayout();
//    myPerceptronWidget->createControllerConnections();
//    myPerceptronWidget->initializeUI(0);
//    myPerceptronWidget->show();


    JsonHelper jsonHelperObj;
    jsonHelperObj.demo();


    return a.exec();
}
