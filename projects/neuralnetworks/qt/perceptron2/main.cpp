#include <QApplication>
#include "perceptronjsonmodel.h"
#include "perceptronwidget.h"
#include "perceptronweightwidget.h"
#include "perceptroncontroller.h"
#include <QDebug>

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronJsonModel myPerceptronJsonModel("../../../python/matrix_dotprod.py");
    PerceptronWidget* myPerceptronWidget = new PerceptronWidget(myPerceptronJsonModel);
    PerceptronWeightWidget m_PerceptronWeightWidget(myPerceptronJsonModel);

    PerceptronController myPerceptronController(*myPerceptronWidget, m_PerceptronWeightWidget, myPerceptronJsonModel);

    return a.exec();
}
