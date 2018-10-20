#include "mainwindow.h"
#include <QApplication>
#include "logicmodel.h"
#include "controller.h"
#include <QDebug>


int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    LogicModel objLogicModel;

    MainWindow objMainWindow;

    Controller objController(objLogicModel, objMainWindow);

    objMainWindow.show();

    return a.exec();
}
