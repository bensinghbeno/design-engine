#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include "perceptronoutputwidget.h"

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

private:
  PerceptronWidget* m_pPerceptronOutPutWidget;
};

#endif // MAINWINDOW_H
