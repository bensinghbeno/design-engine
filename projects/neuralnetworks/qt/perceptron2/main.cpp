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
    myPerceptronWidget->initializeUI(0);
    myPerceptronWidget->show();



    JsonLoad jsonloadobj;
    jsonloadobj.demo();


    return a.exec();
}
