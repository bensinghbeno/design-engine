#include "perceptronoutputwidget.h"

PerceptronOutPutWidget::PerceptronOutPutWidget(QWidget *parent)
  : QWidget(parent)
  , m_parent(parent)
  , outputLabelX(0)
  , outputLabelY(0)
{
    qDebug() << "PerceptronOutPutWidget()";
    //QHBoxLayout* layout = new QHBoxLayout();
    //pOutputLabel = new QLabel("Output_1");

    //layout->addWidget(pOutputLabel);
    //this->setLayout(layout);
    installEventFilter(this);

}

bool PerceptronOutPutWidget::eventFilter(QObject *watched, QEvent *event)
{
    if (watched == this && event->type() == QEvent::Paint)
    {
        QPainter painter;
        painter.begin(this);
        painter.setRenderHint(QPainter::Antialiasing, true);
        painter.setPen(QPen(Qt::black, 12, Qt::DashDotLine, Qt::RoundCap));
        painter.setBrush(QBrush(Qt::green, Qt::SolidPattern));
        painter.drawEllipse(50, this->y(), 100, 100);
        painter.end();
        return true; // return true if you do not want to have the child widget paint on its own afterwards, otherwise, return false.
    }
    return false;
}


void PerceptronOutPutWidget::paintEvent(QPaintEvent *event)
{
   // qDebug() << "pOutputLabel() :: x = "<<this->layout()->geometry().x()<<"y = "<<this->layout()->geometry().y();


//    QPainter painter(this);
//    QPen pen;
//    pen.setWidth(3);
//    pen.setColor(Qt::black);
//    QBrush brush(Qt::yellow);
//    painter.setPen (pen);
//    painter.setBrush(brush);
//    painter.drawEllipse(0, 450, 100, 50);
}

