#include "perceptronjsonmodel.h"
#include "perceptronjsonterminal.h"
#include <QDebug>

PerceptronJsonModel::PerceptronJsonModel(QString pythonEnginePath, QObject *parent)
    : QObject(parent)
{
    m_perceptronJsonTerminal.setPythonEnginePath(pythonEnginePath);

    //demo();
}

void PerceptronJsonModel::sltLayerCountUpdate(int layerCount)
{
    qDebug() << "PerceptronJsonModel::sltLayerCountUpdate() = " << layerCount;

    insertvalue("LAYERCOUNT", QString::number(layerCount));
    //qDebug() << "LAYERCOUNT = " << getvalue("LAYERCOUNT");

}

void PerceptronJsonModel::sltMasterInputCountUpdate(int masterInputCount)
{
    qDebug() << "PerceptronJsonModel::sltMasterInputCountUpdate() = " << masterInputCount;

    insertvalue("MASTERINPUTCOUNT", QString::number(masterInputCount));
    qDebug() << "MASTERINPUTCOUNT = " << getvalue("MASTERINPUTCOUNT");
}

void PerceptronJsonModel::sltCreatePerceptronNetwork()
{
    //qDebug() << "PerceptronJsonModel::sltRequestPerceptronMatrix()";

    int currentLayerCount =  getvalue("LAYERCOUNT").toInt();
    int currentMasterInputCount =  getvalue("MASTERINPUTCOUNT").toInt();

    if ((currentLayerCount < 1) || (currentMasterInputCount < 3))
    {
        qDebug() << "ERROR : Please provide LAYERCOUNT >= 1 & MASTERINPUTCOUNT >= 3";
        return;
    }
    else
    {
        updateJsonModel(currentLayerCount, currentMasterInputCount);

        emit sgnJsonModelUpdated();
        //sendJsonBuffer();
    }

//    if (currentLayerCount != layerCount)
//    {

//        for (int i = 1; i <= layerCount; i++ )
//        {
//            QString layerid = getvalue("L"+ QString::number(i)+"I1");
//            if (layerid.isEmpty())
//            {
//                qDebug() << "PerceptronJsonModel:: layerid - " << layerid << " isEmpty() !!";
//                break;
//            }
//            else
//            {
//                qDebug() << "PerceptronJsonModel:: layerid - " << layerid << " isNotEmpty()";
//            }

//        }



//        sendJsonBuffer();

//    }
//    else
//    {
//        qDebug() << "LAYERCOUNT Indifferent!! " << currentLayerCount;
//    }

    //insertvalue("MASTERINPUTCOUNT", QString::number(masterInputCount));
    //qDebug() << "MASTERINPUTCOUNT = " << getvalue("MASTERINPUTCOUNT");

}

void PerceptronJsonModel::demo()
{
    insertvalue("LAYERCOUNT","1");
    insertvalue("MASTERINPUTCOUNT","3");
    insertvalue("ROWCOUNT_L1","2");
    insertvalue("COLOUMNCOUNT_L1","2");
    qDebug() << "LAYERCOUNT = " << getvalue("LAYERCOUNT");
    m_perceptronJsonTerminal.sendJsonBuffer2Engine(getJsonStringbuffer());

}

void PerceptronJsonModel::sendJsonBuffer()
{
    m_perceptronJsonTerminal.sendJsonBuffer2Engine(getJsonStringbuffer());
}

void PerceptronJsonModel::insertvalue(QString key, QString value)
{

    m_valweight = value;
    m_objlayer.insert(key,m_valweight);

}

QString PerceptronJsonModel::getvalue(QString key)
{
    return m_objlayer.value(key).toString();
}

QString& PerceptronJsonModel::getJsonStringbuffer()
{

    m_docjson.setObject(m_objlayer);
    m_strdocjson =  m_docjson.toJson();
    return m_strdocjson;
}

void PerceptronJsonModel::insertJsonStringbuffer(QString strJson)
{
    m_docjson = QJsonDocument::fromJson(strJson.toUtf8());
    m_objlayer = m_docjson.object();
}

void PerceptronJsonModel::updateJsonModel(int currentMasterLayerCount, int currentMasterInputCount)
{
    QString layerId;
    QString inputId;
    QString inputElementId;
    QString weightId;
    QString weightElementId;

    for (int l = 1 ; l <= currentMasterLayerCount; l++)
    {
        layerId = ("L" + QString::number(l) + "_");

        for (int i = 1 ; i <= currentMasterInputCount; i++)
        {
            // Update Inputs
            inputId = ("I" + QString::number(i));
            inputElementId  = layerId + inputId;
            insertvalue(inputElementId,"0");

            //Update Weights
            for (int w = 1 ; w <= currentMasterInputCount; w++)
            {
                weightId = ("W" + QString::number(w) + QString::number(i));
                weightElementId = layerId + weightId;
                insertvalue(weightElementId,"0");
            }
        }
    }

    insertvalue("L1_I1","16");
    insertvalue("L1_I2","7");
    insertvalue("L1_I3","77");

    qDebug() << " --- Json Model Updated --- \n" << getJsonStringbuffer() ;

}


void PerceptronJsonModel::loadjsonfile(QString filepath)
{
    m_file.setFileName(filepath);
    m_file.open(QIODevice::ReadOnly | QIODevice::Text);
    m_fileBuffer = m_file.readAll();
    m_file.close();

}

void PerceptronJsonModel::readJson(QString filepath)
{
    loadjsonfile(filepath);
    //qWarning() << val;

    //QJsonDocument jsondoc = QJsonDocument::fromJson(m_fileBuffer.toUtf8());
    //QJsonObject sett = jsondoc.object();
    //QJsonValue value = sett.value(QString("appName"));
    //QJsonObject item = value.toObject();
    //QJsonArray test = item["layer1"].toArray();
    //qDebug() << "orig = " << test[2].toString();



    //QString buff2 =  jsondoc.toJson();
    //QJsonDocument jsondoc2 = QJsonDocument::fromJson(buff2.toUtf8());
    //QJsonObject sett2 = jsondoc2.object();
    //QJsonValue value2 = sett2.value(QString("appName"));
    //QJsonObject item2 = value2.toObject();
    //QJsonArray test2 = item2["layer1"].toArray();
    //qDebug() << "orig2 = " << test2[2].toString();
}
