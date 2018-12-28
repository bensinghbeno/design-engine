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

public slots:

    void sltSetIp(QString text);
    void sltSetPort(quint16 port);
    void sltSetMessage(QString text);

private:
    Ui::MainWindow *ui;
};

#endif // MAINWINDOW_H
