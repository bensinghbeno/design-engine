#ifndef PERCEPTRONWIDGET_H
#define PERCEPTRONWIDGET_H

#include <QWidget>
#include <QtCore>
#include <QLabel>
#include <QSpinBox>
#include <QLayout>

class PerceptronWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronWidget(QWidget *parent = 0);
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
