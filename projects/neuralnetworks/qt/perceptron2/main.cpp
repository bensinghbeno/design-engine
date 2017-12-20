#include <QApplication>
#include <QDebug>

#include "perceptronwidget.h"
#include "perceptronjsonmodel.h"
#include "perceptroncontroller.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();
    PerceptronJsonModel myPerceptronJsonModel("/home/ben/engine/design-engine/projects/python/matrix_dotprod.py");
    PerceptronController myPerceptronController(*myPerceptronWidget, myPerceptronJsonModel);

    return a.exec();
}
