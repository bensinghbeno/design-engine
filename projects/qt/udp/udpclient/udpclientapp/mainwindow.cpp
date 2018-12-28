#include "mainwindow.h"
#include "ui_mainwindow.h"
#include <QDebug>

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    setWindowTitle("UdpClientApp");

    connect(ui->teServerIp,SIGNAL(textChanged()),this,SLOT(sltIpChanged()));
    connect(ui->teServerPort,SIGNAL(textChanged()),this,SLOT(sltPortChanged()));
    connect(ui->pbSendData,SIGNAL(clicked(bool)),this,SLOT(sltSendData(bool)));
}

void MainWindow::sltIpChanged()
{
    qDebug() << "MainWindow::sltIpChanged()  = " << ui->teServerIp->toPlainText();
    emit sgnIpChanged(ui->teServerIp->toPlainText());
}

void MainWindow::sltPortChanged()
{
    qDebug() << "MainWindow::sltPortChanged()  = " << ui->teServerPort->toPlainText().toInt();
    emit sgnPortChanged(ui->teServerPort->toPlainText().toInt());
}

void MainWindow::sltSendData(bool pressed)
{
    qDebug() << "MainWindow::sltSendData()  = " << ui->teData2Send->toPlainText();
    emit sgnSendData(ui->teData2Send->toPlainText());

}

MainWindow::~MainWindow()
{
    delete ui;
}
