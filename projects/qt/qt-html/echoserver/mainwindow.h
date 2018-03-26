#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QDialog>
#include "ui_dialog.h"



class MainWindow : public QDialog
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();
    Ui::Dialog *ui;

Q_SIGNALS:
    void sigSendToClient(QString message);


public Q_SLOTS:

    void sltSendTextClicked();
    void sltUpdateMessageReceived(QString message);


};

#endif // MAINWINDOW_H
