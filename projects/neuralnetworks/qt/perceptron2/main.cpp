#include <QApplication>
#include <QDebug>

#include "perceptronwidget.h"
#include "perceptronjsonmodel.h"
#include "perceptroncontroller.h"
#include "perceptronjsonterminal.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    PerceptronWidget* myPerceptronWidget = new PerceptronWidget();
    PerceptronJsonTerminal myPerceptronJsonTerminal("/home/ben/engine/design-engine/projects/python/matrix_dotprod.py");
    PerceptronJsonModel myPerceptronJsonModel(myPerceptronJsonTerminal);
    PerceptronController myPerceptronController(*myPerceptronWidget, myPerceptronJsonModel);

    return a.exec();
}
