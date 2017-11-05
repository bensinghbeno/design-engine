#ifndef PERCEPTRONWIDGET_H
#define PERCEPTRONWIDGET_H

#include <QWidget>
#include <QtCore>
#include <QtGui>

class PerceptronWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronWidget(int rows,QWidget *parent = 0);
    ~PerceptronWidget();
    QVector<QSpinBox*> m_VecSpinBoxInputs;
    QVector<QLabel*> m_VecLabelOutputs ;
    QGridLayout m_PerceptronGridLayout;
    void PlaceOutputWidgets();
    QGridLayout& getBoxLayout();

    inline void cleanupInputs();
    inline void cleanupOutputs();

    int mRowSize;
    QVBoxLayout m_MainWindowVLayout;

public slots:
    void sltCreateInputWidgets(int rows);


};


#endif
