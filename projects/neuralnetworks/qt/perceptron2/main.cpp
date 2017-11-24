#include <QApplication>
#include "perceptronwidget.h"
#include "perceptronmainwindow.h"

#include <QDebug>
#include "jsonhelper.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronMainWindow* pPerceptronMainWindow = new PerceptronMainWindow();

    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();
    myPerceptronWidget->createLayout();
    myPerceptronWidget->createControllerConnections();
    pPerceptronMainWindow->addPerceptronWidget(*myPerceptronWidget);
    myPerceptronWidget->initializeUI(0, "LAYER1");

    pPerceptronMainWindow->show();



    JsonLoad jsonloadobj;
    jsonloadobj.demo();




    return a.exec();
}
