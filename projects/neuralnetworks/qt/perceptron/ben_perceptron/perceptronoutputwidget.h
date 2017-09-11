#ifndef PERCEPTRONOUTPUTWIDGET_H
#define PERCEPTRONOUTPUTWIDGET_H

#include <QWidget>
#include <QtGui>

class PerceptronWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronWidget(QWidget *parent = 0);
    void paintEvent(QPaintEvent *event);
    bool eventFilter(QObject *watched, QEvent *event);

private:
    QPushButton*    m_pOutputLabel;
    QHBoxLayout*    pPerceptronLayout;
    QLabel*         pInputLabel;
    QSpinBox*       pInputBox;
    QLabel*         WeightLabel;
    QSpinBox*       pWeightBox;
    QSpacerItem*    pPerceptronSpacer1;
    QSpacerItem*    pPerceptronSpacer2;
    QSpacerItem*    pPerceptronSpacer3;

signals:

public slots:
};

#endif // PERCEPTRONOUTPUTWIDGET_H
