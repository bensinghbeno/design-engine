#ifndef PERCEPTRONOUTPUTWIDGET_H
#define PERCEPTRONOUTPUTWIDGET_H

#include <QWidget>
#include <QtGui>

class PerceptronOutPutWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronOutPutWidget(QWidget *parent = 0);
    void paintEvent(QPaintEvent *event);
    bool eventFilter(QObject *watched, QEvent *event);
    QLabel* pOutputLabel;
    int outputLabelX;
    int outputLabelY;
    QWidget* m_parent;


signals:

public slots:
};

#endif // PERCEPTRONOUTPUTWIDGET_H
