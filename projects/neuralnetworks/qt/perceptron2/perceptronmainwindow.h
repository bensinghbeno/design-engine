#ifndef PERCEPTRONMAINWINDOW_H
#define PERCEPTRONMAINWINDOW_H

#include <QWidget>
#include "perceptronwidget.h"


class PerceptronMainWindow : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronMainWindow(QWidget *parent = 0);
    void addPerceptronWidget(PerceptronWidget &pWidget);

    QVector<PerceptronWidget*> m_VecPerceptronWidgets;
    QVBoxLayout m_MainWindowVLayout;

signals:

public slots:
};

#endif // PERCEPTRONMAINWINDOW_H
