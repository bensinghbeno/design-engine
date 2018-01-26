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

class PerceptronJsonModel;

class PerceptronWeightWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronWeightWidget(PerceptronJsonModel& perceptronJsonModel, QWidget *parent = 0);

    //DataModel Interface
    PerceptronJsonModel& m_PerceptronJsonModel;

    QHBoxLayout m_modelMainHLayout;
    QList<QSpinBox*> m_listWeightWidgets;


signals:

public slots:
    void sltCreatePerceptronWeightWidgets();

};

#endif // PERCEPTRONDATAWIDGET_H
