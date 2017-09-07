#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>

namespace Ui {
class MainWindow;
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = 0);
    ~MainWindow();

private:
    Ui::MainWindow *ui;
    QList<QWidget *> l;
    static void RemoveWidget(QWidget *pWidget);

private slots:
    void InputsChanged(QString inputs);

};

#endif // MAINWINDOW_H
