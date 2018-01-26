#include "perceptronwidget.h"
#include "perceptronjsonmodel.h"

PerceptronWidget::PerceptronWidget(PerceptronJsonModel& perceptronJsonModel, QWidget *parent)
    : QWidget(parent)
    , m_PerceptronJsonModel(perceptronJsonModel)
    , mRowSize(0)
    , m_magicCount(0)
    , m_startPainting(false)
{
    createMasterLayout();
    initializeUi(0);
    show();
}

void PerceptronWidget::createLayerLayout()
{
    //MainToolBox
    m_MainWindowHToolBarLayout.addWidget(new QLabel("   Perceptron Toolbox    "));
    m_MainWindowHToolBarLayout.addWidget(new QLabel("Total Layers = "));
    m_MainWindowHToolBarLayout.addWidget(&m_SpinBoxLayerCount);
    m_MainWindowHToolBarLayout.addWidget(&m_labelMasterInputCount);
    m_MainWindowHToolBarLayout.addWidget(&m_sbLayerMasterInputCount);
    m_MainWindowHToolBarLayout.addWidget(&m_pbCreateMatrix);
    m_layoutVboxMain.addLayout(&m_MainWindowHToolBarLayout);

    m_pFrameLineSepMainToolBox = new QFrame(this);
    m_pFrameLineSepMainToolBox->setFrameShape(QFrame::HLine);
    m_pFrameLineSepMainToolBox->setFrameShadow(QFrame::Sunken);
    m_layoutVboxMain.addWidget(m_pFrameLineSepMainToolBox);

    //LayerToolBox
    m_layoutHboxMenu.addWidget(&m_labelLayerName);
    //m_layoutHboxMenu.addWidget(&m_labelInputCount);
    //m_layoutHboxMenu.addWidget(&m_sbLayerInputCount);
    //m_layoutHboxMenu.addWidget(&m_labelOutputCount);
    //m_layoutHboxMenu.addWidget(&m_sbLayerOutputCount);

    m_pSpacerLayerToolBox = new QSpacerItem(100,50);
    m_layoutHboxMenu.addSpacerItem(m_pSpacerLayerToolBox);

    m_layoutVboxMain.addLayout(&m_layoutHboxMenu);
    m_layoutVboxMain.addLayout(&m_LayersHLayout);
    m_LayersHLayout.addLayout(&m_MasterInputLayout);
    m_LayersHLayout.addLayout(&m_layoutgridLayer);
    m_LayersHLayout.addWidget(&m_btnMasterOutput);
    m_btnMasterOutput.hide();


    this->setLayout(&m_layoutVboxMain);
}

void PerceptronWidget::createMasterLayout()
{
    createLayerLayout();

    //mp_pbMasterOutput = new QPushButton();
    //m_LayersHLayout.addWidget(mp_pbMasterOutput);
}


void PerceptronWidget::initializeUi(int rowcount)
{
    QString layername = "Layer 1   |   ";
    QString strlayerMagiccount = "Master Inputs = ";
    QString strlayerInputcount = "Inputs = ";
    QString strlayerOutputcount = "Outputs = ";

    m_strOutputItemStylesheet = ("QPushButton {"
                                 "background-color: lightgreen;"
                                 "border-style: solid;"
                                 "border-width:3px;"
                                 "border-radius:20px;"
                                 "border-color: black;"
                                 "max-width:40px;"
                                 "max-height:40px;"
                                 "min-width:40px;"
                                 "min-height:40px;"
                                   "}");

    m_sbLayerInputCount.setMaximumWidth(70);
    m_sbLayerInputCount.setValue(rowcount);
    //m_labelLayerName.setText(layername);
    m_labelMasterInputCount.setText(strlayerMagiccount);
    m_labelInputCount.setText(strlayerInputcount);
    m_labelOutputCount.setText(strlayerOutputcount);
    m_sbLayerMasterInputCount.setFocus();

    m_btnMasterOutput.setStyleSheet(m_strOutputItemStylesheet);
    m_btnMasterOutput.setText("100");

    m_pbCreateMatrix.setText("Create Network");
    m_layoutgridLayer.setSpacing(50);
    this->setWindowTitle("Perceptron Graphic Widget");

}

void PerceptronWidget::sltCreatePerceptronMagicWidgets(int count)
{
    m_magicCount = count;
    emit sltCreateInputWidgets();
}


////////////////////// Main Network Creation/////////////////////

void PerceptronWidget::sltCreatePerceptronWidgets()
{
    m_masterInputCount   =   m_PerceptronJsonModel.getvalue("MASTERINPUTCOUNT").toInt();
    m_layerCount         =   m_PerceptronJsonModel.getvalue("LAYERCOUNT").toInt();

    createMasterInputOutputWidgets();
    createLayerWidgets();
    m_startPainting = true;
}

void PerceptronWidget::createMasterInputOutputWidgets()
{
    cleanupDynamicWidgets();

    for(int it = 1; it <= m_masterInputCount; it++)
    {
        QString inputElementname = ("I" + QString::number(it));
        auto value =  m_PerceptronJsonModel.getvalue(inputElementname).toInt();

        QSpinBox* pSpinBox = new QSpinBox();
        m_VecSpinBoxMasterInputs.push_back(pSpinBox);
        m_MasterInputLayout.addWidget(pSpinBox);
        pSpinBox->setMaximumWidth(50);
        pSpinBox->setValue(value);
        pSpinBox->setObjectName(inputElementname);
        list_inputs.append(pSpinBox);
        connect(pSpinBox,SIGNAL(valueChanged(int)),this,SLOT(sltInputsUpdated(int)));
    }

    m_btnMasterOutput.show();
}

void PerceptronWidget::createLayerWidgets()
{
    // Cleanup Existing Layer Widgets
    for(TLayerWidget* listLayerWidgets: m_listLayerOutputWidgets)
    {
        for(const QPushButton* outputwidget: (*listLayerWidgets))
        {
            delete(outputwidget);
        }
        delete(listLayerWidgets);
    }
    m_listLayerOutputWidgets.clear();



    for(int layercolumn = 0; layercolumn < m_layerCount; layercolumn++)
    {
        TLayerWidget* layerwidget = new TLayerWidget;

        for(int inputrow = 0; inputrow < m_masterInputCount; inputrow++)
        {
            QPushButton* pPushButton = new QPushButton();
            pPushButton->setStyleSheet(m_strOutputItemStylesheet);
            m_layoutgridLayer.addWidget(pPushButton,inputrow, layercolumn);
            pPushButton->setMaximumWidth(50);
            layerwidget->append(pPushButton);
        }

        m_listLayerOutputWidgets.push_back(layerwidget);
    }

    update();
}

////////////////////// Widget Data Updates /////////////////////

void PerceptronWidget::sltInputsUpdated(int inputvalue)
{
    qDebug() << "InputWidget - name = " << sender()->objectName() << " value = " << inputvalue;
    QString inputElementname = sender()->objectName();
    m_PerceptronJsonModel.insertvalue(inputElementname, QString::number(inputvalue));
}


void PerceptronWidget::paintEvent(QPaintEvent* /*event*/)
{

    qDebug() << "PerceptronWidget::paintEvent()";

    QPainter painter(this);

    if (!(list_inputs.isEmpty()) && !(m_listLayerOutputWidgets.isEmpty()))
    {

        // Draw lines from Inputs to Layer
        for(const QWidget* from: list_inputs)
        {

            for(const QPushButton* to: *(m_listLayerOutputWidgets.front()))
            {
                QPoint start =  from->mapToGlobal(from->rect().topRight() +  QPoint(0, from->height()/2));
                QPoint end = to->mapToGlobal(to->rect().topLeft() +  QPoint(0, to->height()/2));
                painter.drawLine(mapFromGlobal(start), mapFromGlobal(end));
            }

        }

        // Draw lines from last Layer to Output
        for(const QPushButton* from: *(m_listLayerOutputWidgets.last()))
        {
            QPoint start =  from->mapToGlobal(from->rect().topRight() +  QPoint(0, from->height()/2));
            QPoint end = m_btnMasterOutput.mapToGlobal(m_btnMasterOutput.rect().topLeft() +  QPoint(0, m_btnMasterOutput.height()/2));
            painter.drawLine(mapFromGlobal(start), mapFromGlobal(end));
        }


        // Draw lines within Layer
        for(QList<TLayerWidget*>::iterator it = m_listLayerOutputWidgets.begin(); it != m_listLayerOutputWidgets.end(); it++)
        {
            auto layerFrom = *it;
            auto layerTo = *(it+1);

            if ( (it+1) != m_listLayerOutputWidgets.end())
            {
                qDebug() << "Draw within Layer";

                for(const QPushButton* from: (*layerFrom))
                {
                    for(const QPushButton* to: (*layerTo))
                    {
                        QPoint start =  from->mapToGlobal(from->rect().topRight() +  QPoint(0, from->height()/2));
                        QPoint end = to->mapToGlobal(to->rect().topLeft() +  QPoint(0, to->height()/2));
                        painter.drawLine(mapFromGlobal(start), mapFromGlobal(end));
                    }
                }
            }



        }
    }
}


void PerceptronWidget::sltCreateInputWidgets()
{
    cleanupDynamicWidgets();

    int inputrows;
    int outputrows;

    if (m_magicCount != 0)
    {
        inputrows = outputrows = m_magicCount;
    }
    else
    {
        inputrows = m_sbLayerInputCount.value();
        outputrows = m_sbLayerOutputCount.value();
    }

    for(int it = 0; it < inputrows; it++)
    {
        QSpinBox* pSpinBox = new QSpinBox();
        m_VecSpinBoxInputs.push_back(pSpinBox);
        m_layoutgridLayer.addWidget(pSpinBox,it, 0);
        pSpinBox->setMaximumWidth(50);
        list_inputs.append(pSpinBox);
    }

    for(int it = 0; it < outputrows; it++)
    {
        QPushButton* pbtnOutput = new QPushButton();
        m_vecbtnOutputs.push_back(pbtnOutput);
        m_layoutgridLayer.addWidget(pbtnOutput,it, 1);
        pbtnOutput->setText("77");
        pbtnOutput->setStyleSheet(m_strOutputItemStylesheet);
        list_outputs.append(pbtnOutput);
    }

    m_layoutgridLayer.setColumnMinimumWidth(0,100);
    update();
}


void PerceptronWidget::addWidgets(const QWidget * from, const QWidget * to)
{
    list.append(sLayerLineWidgets{from , to});
    update();
}

inline void PerceptronWidget::cleanupDynamicWidgets()
{
    m_listMasterInputs.clear();


    list_inputs.clear();
    list_outputs.clear();

    for (QVector<QSpinBox*>::iterator it = m_VecSpinBoxMasterInputs.begin() ; it != m_VecSpinBoxMasterInputs.end(); ++it)
    {
        delete (*it);
    }
    m_VecSpinBoxMasterInputs.clear();

    for (QVector<QSpinBox*>::iterator it = m_VecSpinBoxInputs.begin() ; it != m_VecSpinBoxInputs.end(); ++it)
    {
        delete (*it);
    }
    m_VecSpinBoxInputs.clear();

    for (QVector<QPushButton*>::iterator it = m_vecbtnOutputs.begin() ; it != m_vecbtnOutputs.end(); ++it)
    {
        delete (*it);
    }
    m_vecbtnOutputs.clear();
}


void PerceptronWidget::PlaceOutputWidgets()
{

}

PerceptronWidget::~PerceptronWidget()
{

    cleanupDynamicWidgets();

}
