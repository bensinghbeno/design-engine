#ifndef PERCEPTRONOUTPUTWIDGET_H
#define PERCEPTRONOUTPUTWIDGET_H
//TBM CHANGE FILENAME

#include <QWidget>
#include <QtGui>
#include <QVector>
#include "perceptronconnector.h"
#include "perceptronconnectors.h"

class PerceptronWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronWidget(QWidget *parent, uint aIndex);
    bool eventFilter(QObject *object, QEvent *event);

    ~PerceptronWidget();

private:
    //View Objects
    uint            m_Index;
    QLabel*         m_pInputLabel;
    QSpinBox*       m_pInputSpinBox;
    QPushButton*    m_pOutputLabel;
    QSpacerItem*    m_pPerceptronSpacer1;
    QSpacerItem*    m_pPerceptronSpacer2;
    QVBoxLayout*    m_pPerceptronVLayout;
    QHBoxLayout*    m_pPerceptronHLayout;
    QHBoxLayout*    m_pWeightBoxLayout;
    QHash<QString, QVector<QHBoxLayout*> > m_Input2WeightBoxLayouts_HashMap;
    QVector<QHBoxLayout*> m_VecWeightBoxLayouts;
    PerceptronConnector* m_pPerceptronConnector;
    PerceptronConnectors* m_pPerceptronConnectors;


    // Datamodel Objects
    QVector<QLabel*> m_VecInputLabels;
    QVector<QLabel*> m_VecOutputLabels;
    QHash<QString, QString> m_IO2Weights_HashMap;

public:
    QLabel* getInputLabel()
    {
      return m_pInputLabel;
    }

signals:

public slots:
};

#endif // PERCEPTRONOUTPUTWIDGET_H
