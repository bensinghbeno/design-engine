#include "mainwindow.h"
#include "ui_mainwindow.h"

#include <QGridLayout>
#include <QPushButton>

#include <QDebug>

static Ui::MainWindow *pStaticUi;

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    ui(new Ui::MainWindow)
{
    ui->setupUi(this);
    QGridLayout *lay = new QGridLayout;
    ui->drawWidget->setLayout(lay);
    for(int i=0; i < 20; i++){
        for(int j=0; j < 2; j++){
            auto btn = new QPushButton(QString("%1,%2").arg(i).arg(j), this);
            btn->setMaximumSize(QSize(60, 60));
            lay->addWidget(btn, i, j);
            l.append(btn);
        }
        ui->drawWidget->addWidgets(l.at(i*2), l.at(i*2+1));
    }

    pStaticUi = ui;

    connect(ui->spinBox_NumOfInputs,SIGNAL(valueChanged(QString)), this, SLOT(InputsChanged(QString)));

}


void MainWindow::InputsChanged(QString inputs)
{
    this->ui->label_Inputs->setText(inputs);
}

void MainWindow::RemoveWidget(QWidget* pWidget)
{
    pStaticUi->drawWidget->layout()->removeWidget(pWidget);
}



MainWindow::~MainWindow()
{
    delete ui;
}
