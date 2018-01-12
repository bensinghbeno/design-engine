#ifndef PERCEPTRONWIDGET_H
#define PERCEPTRONWIDGET_H

#include <QWidget>
#include <QtCore>
#include <QLabel>
#include <QSpinBox>
#include <QLayout>
#include <QtGui>
#include <QPushButton>
#include <QLine>
#include "perceptronweightwidget.h"

class PerceptronJsonModel;

class PerceptronWidget : public QWidget
{
    Q_OBJECT

public:
    explicit PerceptronWidget(PerceptronJsonModel& perceptronJsonModel, QWidget *parent = 0);
    ~PerceptronWidget();

    PerceptronWeightWidget m_PerceptronDataWidget;

    //////////Layer////////////////

    //DataModel Interface
    PerceptronJsonModel& m_PerceptronJsonModel;


    //Data
    int mRowSize;
    int m_magicCount;
    bool m_startPainting;

    //Widgets
    QVector<QSpinBox*> m_VecSpinBoxMasterInputs;
    QPushButton m_btnMasterOutput;

    QSpinBox m_SpinBoxLayerCount;
    QPushButton m_pbCreateMatrix;
    QLabel m_labelLayerName;
    QLabel m_labelMasterInputCount;
    QSpinBox m_sbLayerMasterInputCount;
    QLabel m_labelInputCount;
    QLabel m_labelOutputCount;
    QSpinBox m_sbLayerInputCount;
    QSpinBox m_sbLayerOutputCount;

    QVector<QSpinBox*> m_VecSpinBoxInputs;

    typedef QList<QPushButton*> TLayerWidget;
    QList<TLayerWidget*> m_listLayerOutputWidgets;


    QVector<QPushButton*> m_vecbtnOutputs;
    QFrame* m_pFrameLineSepMainToolBox;
    QSpacerItem* m_pSpacerLayerToolBox;

    //Stylesheets
    QString m_strOutputItemStylesheet;

    //Layouts
    QVBoxLayout m_MainWindowVLayout;
    QHBoxLayout m_MainWindowHToolBarLayout;
    QVBoxLayout m_MasterInputLayout;
    QHBoxLayout m_LayersHLayout;
    QVBoxLayout m_layoutVboxMain;
    QHBoxLayout m_layoutHboxMenu;
    QGridLayout m_layoutgridLayer;

    //UI Operations
    void createLayerLayout();
    void initializeUi(int rowcount);
    void PlaceOutputWidgets();
    inline void cleanupDynamicWidgets();
    inline void cleanupOutputs();
    void addWidgets(const QWidget *from, const QWidget *to);
    void createMasterInputOutputWidgets();
    void createLayerWidgets();




public slots:
    void sltCreateInputWidgets();
    void sltCreatePerceptronMagicWidgets(int count);
    void sltCreatePerceptronWidgets();

protected:
    void paintEvent(QPaintEvent*);

private:
    struct sLayerLineWidgets
    {
        const QWidget* from;
        const QWidget* to;
    };

    QList<sLayerLineWidgets> list;

    QList<const QWidget*> list_inputs;
    QList<const QWidget*> m_listMasterInputs;
    QList<const QWidget*> list_outputs;
    int m_masterInputCount;
    int m_layerCount;


public:

    //UI Operations
    void createMasterLayout();

};


#endif
