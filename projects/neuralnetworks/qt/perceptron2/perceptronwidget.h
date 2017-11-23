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

    //Widgets
    QSpinBox m_SpinBoxRowCount;
    QLabel m_labelLayerName;

    //IO
    QVector<QSpinBox*> m_VecSpinBoxInputs;
    QVector<QLabel*> m_VecLabelOutputs ;

    //Layouts
    QVBoxLayout m_layoutVboxMain;
    QHBoxLayout m_layoutHboxMenu;
    QGridLayout m_layoutgridLayer;

    void createLayout();
    void createControllerConnections();
    void initializeUI(int rowcount, QString layername);

    void PlaceOutputWidgets();
    inline void cleanupInputs();
    inline void cleanupOutputs();

    QVBoxLayout& getMainLayout();


    int mRowSize;
    QVBoxLayout m_MainWindowVLayout;

public slots:
    void sltCreateInputWidgets(int rows);


};


#endif
