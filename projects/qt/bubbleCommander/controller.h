#ifndef CONTROLLER_H
#define CONTROLLER_H

#include <QObject>
#include "logicmodel.h"
#include "mainwindow.h"
#include "ui_mainwindow.h"

class Controller : public QObject
{
    Q_OBJECT
public:
    explicit Controller(LogicModel& logicModel, MainWindow& mainWindow, QObject *parent = 0);
    LogicModel& m_LogicModel;
    MainWindow& m_MainWindow;

signals:

public slots:
};

#endif // CONTROLLER_H
