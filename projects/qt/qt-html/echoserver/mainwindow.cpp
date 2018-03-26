#include "mainwindow.h"
#include <QtCore/QDebug>

MainWindow::MainWindow(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::Dialog)
{
    ui->setupUi(this);
    setWindowTitle("Foreview Technologies - IOT Web Server Application");
    setMinimumWidth(500);
    QObject::connect(ui->pbSendToClient,SIGNAL(clicked(bool)),this,SLOT(sltSendTextClicked()));

}

void MainWindow::sltSendTextClicked()
{
    qDebug() << "MainWindow::sltSendTextClicked()";
    emit sigSendToClient(ui->teStrToSend->toPlainText());

}

void MainWindow::sltUpdateMessageReceived(QString message)
{
    qDebug() << "MainWindow::sltUpdateMessageReceived()";
    ui->teStrRecFromClient->append(message);

}


MainWindow::~MainWindow()
{
    delete ui;
}
