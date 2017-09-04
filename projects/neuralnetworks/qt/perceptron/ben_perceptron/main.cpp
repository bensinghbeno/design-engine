#include "mainwindow.h"
#include <QApplication>
#include <QtGui>

int main(int argc, char *argv[])
{
  QApplication a(argc, argv);
  MainWindow w;




  QHBoxLayout* pPerceptronLayout = new QHBoxLayout();
  QLabel* pInputLabel = new QLabel("Input_1");
  QSpinBox* pInputBox = new QSpinBox();
  QLabel* WeightLabel= new QLabel("Weight_1");
  QSpinBox* pWeightBox = new QSpinBox();
  QLabel* pOutputLabel = new QLabel("Output_1");
  QSpacerItem* pPerceptronSpacer1 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
  QSpacerItem* pPerceptronSpacer2 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
  QSpacerItem* pPerceptronSpacer3 = new QSpacerItem(100,1, QSizePolicy::Expanding, QSizePolicy::Ignored);
  QTextEdit* pPerceptronOutput = new QTextEdit();
  pPerceptronOutput->setMaximumSize(50,40);
  pPerceptronLayout->addWidget(pInputLabel);
  pPerceptronLayout->addWidget(pInputBox);
  pPerceptronLayout->addSpacerItem(pPerceptronSpacer1);
  pPerceptronLayout->addWidget(WeightLabel);
  pPerceptronLayout->addWidget(pWeightBox);
  pPerceptronLayout->addSpacerItem(pPerceptronSpacer2);
  pPerceptronLayout->addWidget(pOutputLabel);
  pPerceptronLayout->addWidget(pPerceptronOutput);
  pPerceptronLayout->addSpacerItem(pPerceptronSpacer3);





  w.setGeometry(1300,100,600,800);
  w.centralWidget()->setLayout(pPerceptronLayout);
  w.show();
  return a.exec();
}
