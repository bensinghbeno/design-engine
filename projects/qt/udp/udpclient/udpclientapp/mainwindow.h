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
    void sltIpChanged();
    void sltPortChanged();
    void sltSendData(bool pressed);

signals:
    void sgnIpChanged(QString ip);
    void sgnPortChanged(quint16 port);
    void sgnSendData(QString data);

private:
    Ui::MainWindow *ui;
};

#endif // MAINWINDOW_H
