#include <QApplication>
#include "perceptronwidget.h"

#include <QDebug>
#include "jsonhelper.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();
    myPerceptronWidget->createLayout();
    myPerceptronWidget->createControllerConnections();
    myPerceptronWidget->initializeUI(0, "Layer 1 :: Count = ");
    myPerceptronWidget->show();



    JsonLoad jsonloadobj;
    jsonloadobj.demo();


    return a.exec();
}
