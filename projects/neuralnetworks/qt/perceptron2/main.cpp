#include <QApplication>
#include "perceptronwidget.h"
#include "perceptronmainwindow.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronMainWindow* pPerceptronMainWindow = new PerceptronMainWindow();

    PerceptronWidget* myPerceptronWidget = new PerceptronWidget(10);

    pPerceptronMainWindow->addPerceptronWidget(*myPerceptronWidget);

    pPerceptronMainWindow->show();

    return a.exec();
}
