#include "mainwindow.h"
#include <QApplication>
#include <QtGui>
#include "perceptronoutputwidget.h"


int main(int argc, char *argv[])
{
  QApplication a(argc, argv);
  MainWindow w;


  PerceptronOutPutWidget* pPerceptronOutPutWidget = new PerceptronOutPutWidget();
  pPerceptronOutPutWidget->setMinimumSize(400,400);

  QPixmap pm(100,100);
  pm.fill(Qt::transparent);
  QPainter p(&pm);
  p.setRenderHint(QPainter::Antialiasing, true);
  QPen pen(Qt::blue, 2);
  p.setPen(pen);
  QBrush brush(Qt::green);
  p.setBrush(brush);
  p.drawEllipse(10, 10, 80, 80);
  QLabel l;
  l.setPixmap(pm);


  QHBoxLayout* pPerceptronLayout = new QHBoxLayout();
  QLabel* pInputLabel = new QLabel("Input_1");
  QSpinBox* pInputBox = new QSpinBox();
  QLabel* WeightLabel= new QLabel("Weight_1");
  QSpinBox* pWeightBox = new QSpinBox();


  QSpacerItem* pPerceptronSpacer1 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
  QSpacerItem* pPerceptronSpacer2 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
  QSpacerItem* pPerceptronSpacer3 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
  pPerceptronLayout->addWidget(pInputLabel);
  pPerceptronLayout->addWidget(pInputBox);
  pPerceptronLayout->addSpacerItem(pPerceptronSpacer1);
  pPerceptronLayout->addWidget(WeightLabel);
  pPerceptronLayout->addWidget(pWeightBox);
  pPerceptronLayout->addSpacerItem(pPerceptronSpacer2);
  pPerceptronLayout->addWidget(&l);
  pPerceptronLayout->addSpacerItem(pPerceptronSpacer3);





  w.setGeometry(1300,100,900,1000);
  w.centralWidget()->setLayout(pPerceptronLayout);
  w.show();
  return a.exec();
}
