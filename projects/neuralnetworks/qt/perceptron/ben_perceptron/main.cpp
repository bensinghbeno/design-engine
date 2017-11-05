#include "mainwindow.h"
#include <QApplication>
#include <QtGui>
#include "perceptronwidget.h"
#include "datamodel.h"
#include "controller.h"



int main(int argc, char *argv[])
{
  QApplication a(argc, argv);

  MainWindow* viewMainWindow = new MainWindow();

//  DataModel   perceptronDataModel;

//  Controller  perceptronController(0, &perceptronDataModel, &viewMainWindow);

  PerceptronWidget* perceptronWidget = new PerceptronWidget(viewMainWindow, 1);
  //perceptronWidget->show();

  viewMainWindow->show();




  return a.exec();
}
