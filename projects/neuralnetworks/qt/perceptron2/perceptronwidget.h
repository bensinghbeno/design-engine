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


class PerceptronWidget : public QWidget
{
    Q_OBJECT

public:
    explicit PerceptronWidget(QWidget *parent = 0);
    ~PerceptronWidget();

    //////////Layer////////////////

    //Data
    int mRowSize;
    int m_magicCount;

    //Widgets
    QSpinBox m_SpinBoxLayerCount;
    QPushButton m_pbCreateMatrix;
    QLabel m_labelLayerName;
    QLabel m_labelMagicCount;
    QSpinBox m_sbLayerMagicCount;
    QLabel m_labelInputCount;
    QLabel m_labelOutputCount;
    QSpinBox m_sbLayerInputCount;
    QSpinBox m_sbLayerOutputCount;
    QVector<QSpinBox*> m_VecSpinBoxInputs;
    QVector<QPushButton*> m_vecbtnOutputs;
    QFrame* m_pFrameLineSepMainToolBox;
    QSpacerItem* m_pSpacerLayerToolBox;

    //Stylesheets
    QString m_strOutputLabelStylesheet;

    //Layouts
    QVBoxLayout m_MainWindowVLayout;
    QHBoxLayout m_MainWindowHToolBarLayout;
    QHBoxLayout m_LayersHLayout;
    QVBoxLayout m_layoutVboxMain;
    QHBoxLayout m_layoutHboxMenu;
    QGridLayout m_layoutgridLayer;

    //UI Operations
    void createLayerLayout();
    void createControllerConnections();
    void initializeUI(int rowcount);
    void PlaceOutputWidgets();
    inline void cleanupDynamicWidgets();
    inline void cleanupOutputs();
    void addWidgets(const QWidget *from, const QWidget *to);


public slots:
    void sltCreateInputWidgets();
    void sltCreatePerceptronMagicWidgets(int count);

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
    QList<const QWidget*> list_outputs;

    //////////Master Window////////////////

public:
    QPushButton* mp_pbMasterOutput;

    //UI Operations
    void createMasterLayout();

};


#endif
