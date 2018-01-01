#include <QApplication>
#include "perceptronwidget.h"
#include "perceptronjsonmodel.h"
#include "perceptroncontroller.h"
#include <QDebug>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronJsonModel myPerceptronJsonModel("../../../python/matrix_dotprod.py");
    PerceptronWidget* myPerceptronWidget = new PerceptronWidget(myPerceptronJsonModel);
    PerceptronController myPerceptronController(*myPerceptronWidget, myPerceptronJsonModel);

    return a.exec();
}
