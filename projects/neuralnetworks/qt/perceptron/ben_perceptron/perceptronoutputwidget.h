#ifndef PERCEPTRONOUTPUTWIDGET_H
#define PERCEPTRONOUTPUTWIDGET_H

#include <QWidget>
#include <QtGui>

class PerceptronWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronWidget(QWidget *parent = 0);
    ~PerceptronWidget();

private:
    QPushButton*    m_pOutputLabel;
    QHBoxLayout*    m_pPerceptronLayout;
    QLabel*         m_pInputLabel;
    QSpinBox*       m_pInputSpinBox;
    QLabel*         m_pWeightLabel;
    QSpinBox*       m_pWeightSpinBox;
    QSpacerItem*    m_pPerceptronSpacer1;
    QSpacerItem*    m_pPerceptronSpacer2;
    QSpacerItem*    m_pPerceptronSpacer3;

signals:

public slots:
};

#endif // PERCEPTRONOUTPUTWIDGET_H
