#include "mainwindow.h"
#include <QApplication>
#include "logicmodel.h"
#include "controller.h"


int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    LogicModel objLogicModel;

    MainWindow objMainWindow;
    objMainWindow.show();

    Controller objController(objLogicModel, objMainWindow);


    return a.exec();
}
