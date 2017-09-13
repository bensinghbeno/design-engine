#ifndef CONTROLLER_H
#define CONTROLLER_H

#include <QObject>
#include "datamodel.h"
#include "mainwindow.h"

class Controller : public QObject
{
  Q_OBJECT
public:
  explicit Controller(QObject *parent = 0, DataModel* aDataModel = 0
                      , MainWindow* aMainWindow = 0);
  DataModel*   m_pDataModel;
  MainWindow* m_pMainWindow;

signals:

public slots:
};

#endif // CONTROLLER_H
