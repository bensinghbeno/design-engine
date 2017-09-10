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
    QPushButton* m_pOutputLabel;

signals:

public slots:
};

#endif // PERCEPTRONOUTPUTWIDGET_H
