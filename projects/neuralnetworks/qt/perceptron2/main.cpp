#include "mainwindow.h"
#include <QApplication>
#include "perceptronwidget.h"
#include "perceptronmainwindow.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);
//    MainWindow w;
//    w.show();
    PerceptronMainWindow* pPerceptronMainWindow = new PerceptronMainWindow();

    PerceptronWidget* myPerceptronWidget = new PerceptronWidget(10);

    //pPerceptronMainWindow->addPerceptronWidget(*myPerceptronWidget);
    myPerceptronWidget->show();

    return a.exec();
}
