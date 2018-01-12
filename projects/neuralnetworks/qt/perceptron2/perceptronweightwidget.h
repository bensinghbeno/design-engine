#ifndef PERCEPTRONDATAWIDGET_H
#define PERCEPTRONDATAWIDGET_H

#include <QWidget>
#include <QtCore>
#include <QLabel>
#include <QSpinBox>
#include <QLayout>
#include <QtGui>
#include <QPushButton>
#include <QLine>

class PerceptronWeightWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronWeightWidget(QWidget *parent = 0);
    //~PerceptronDataWidget();

    QHBoxLayout m_modelMainHLayout;

signals:

public slots:
};

#endif // PERCEPTRONDATAWIDGET_H
