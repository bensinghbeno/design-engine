#ifndef PERCEPTRONWIDGET_H
#define PERCEPTRONWIDGET_H

#include <QWidget>
#include <QtCore>
#include <QLabel>
#include <QSpinBox>
#include <QLayout>
#include <QtGui>
#include <QPushButton>


class PerceptronWidget : public QWidget
{
    Q_OBJECT
public:
    explicit PerceptronWidget(QWidget *parent = 0);
    ~PerceptronWidget();

    //Data
    int mRowSize;

    //Widgets
    QSpinBox m_SpinBoxRowCount;
    QLabel m_labelLayerName;
    QVector<QSpinBox*> m_VecSpinBoxInputs;
    QVector<QPushButton*> m_vecbtnOutputs;

    //Stylesheets
    QString m_strOutputLabelStylesheet;


    //Layouts
    QVBoxLayout m_layoutVboxMain;
    QHBoxLayout m_layoutHboxMenu;
    QGridLayout m_layoutgridLayer;

    void createLayout();
    void createControllerConnections();
    void initializeUI(int rowcount, QString layername);

    void PlaceOutputWidgets();
    inline void cleanupLayerWidgets();
    inline void cleanupOutputs();


    QVBoxLayout& getMainLayout();

public slots:
    void sltCreateInputWidgets(int rows);


};


#endif
