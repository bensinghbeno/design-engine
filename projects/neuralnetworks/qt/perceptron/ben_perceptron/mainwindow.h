#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include "perceptronwidget.h"

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
  Q_OBJECT

public:
  explicit MainWindow(QWidget *parent = 0);
  bool eventFilter(QObject *object, QEvent *event);
  Ui::MainWindow *ui;

  ~MainWindow();

public slots:
  void SltAddPerceptron(int aCount);
  void SltInputSet(int aInputVal);
  void SltPerceptronOutputSet(int aIndex, int aOutputVal);

signals:
  void SigInputSet(int aInputIndex,int aInputVal);



private:
  std::vector<PerceptronWidget*> mVecPerceptronWidgets;
};

#endif // MAINWINDOW_H
