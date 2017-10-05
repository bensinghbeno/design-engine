#include "mainwindow.h"
#include <QApplication>
#include <QtGui>
#include "perceptronwidget.h"
#include "datamodel.h"
#include "controller.h"



int main(int argc, char *argv[])
{
  QApplication a(argc, argv);

  MainWindow viewMainWindow;
  viewMainWindow.show();

  DataModel   perceptronDataModel;

  Controller  perceptronController(0, &perceptronDataModel, &viewMainWindow);


  return a.exec();
}
