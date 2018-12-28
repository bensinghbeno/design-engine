#include "mainwindow.h"
#include "ui_mainwindow.h"

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    this->setWindowTitle("UdpServerApp");

    ui->labelIp->setText("0.0.0.0");
    ui->labelPort->setText("0");
    ui->messageBrowser->setText(".........");
}

void MainWindow::sltSetIp(QString text)
{
    ui->labelIp->setText(text);
}

void MainWindow::sltSetPort(quint16 port)
{
    ui->labelPort->setText(QString::number(port));
}

void MainWindow::sltSetMessage(QString text)
{
    ui->messageBrowser->setText(text);
}

MainWindow::~MainWindow()
{
    delete ui;
}
