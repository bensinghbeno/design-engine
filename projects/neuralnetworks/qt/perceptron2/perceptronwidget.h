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
    //explicit PerceptronWidget(QWidget *parent = nullptr);

    ~PerceptronWidget();

    //Data
    int mRowSize;

    //Widgets
    QSpinBox m_SpinBoxRowCount;
    QLabel m_labelLayerName;
    QVector<QSpinBox*> m_VecSpinBoxInputs;
    QVector<QPushButton*> m_vecbtnOutputs;
    QFrame* m_pFrameLineSepMainToolBox;
    QSpacerItem* m_pSpacerLayerToolBox;

    //Stylesheets
    QString m_strOutputLabelStylesheet;

    //Layouts
    QVBoxLayout m_MainWindowVLayout;
    QHBoxLayout m_MainWindowHToolBarLayout;
    QSpinBox m_SpinBoxLayerCount;
    QVBoxLayout m_layoutVboxMain;
    QHBoxLayout m_layoutHboxMenu;
    QGridLayout m_layoutgridLayer;

    //Operations
    void createLayout();
    void createControllerConnections();
    void initializeUI(int rowcount, QString layername);
    void PlaceOutputWidgets();
    inline void cleanupLayerWidgets();
    inline void cleanupOutputs();
    void addWidgets(const QWidget *from, const QWidget *to);

    //Getters
    QVBoxLayout& getMainLayout();

public slots:
    void sltCreateInputWidgets(int rows);

protected:
    void paintEvent(QPaintEvent*);

private:
    struct sLayerLineWidgets
    {
        const QWidget* from;
        const QWidget* to;
    };

    QList<sLayerLineWidgets> list;


};


#endif
