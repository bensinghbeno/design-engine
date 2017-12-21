#include <QApplication>
#include "perceptronwidget.h"
#include "perceptronjsonmodel.h"
#include "perceptroncontroller.h"
#include <QDebug>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();
    PerceptronJsonModel myPerceptronJsonModel("../../../python/matrix_dotprod.py");
    PerceptronController myPerceptronController(*myPerceptronWidget, myPerceptronJsonModel);

    return a.exec();
}
