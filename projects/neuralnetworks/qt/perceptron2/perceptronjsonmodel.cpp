#include "perceptronjsonmodel.h"
#include "perceptronjsonterminal.h"
#include <QDebug>

PerceptronJsonModel::PerceptronJsonModel(QString pythonEnginePath, QObject *parent)
    : QObject(parent)
{
    m_perceptronJsonTerminal.setPythonEnginePath(pythonEnginePath);
    insertvalue("LAYERCOUNT","1");
    insertvalue("MASTERINPUTCOUNT","3");
    insertvalue("ROWCOUNT_L1","2");
    insertvalue("COLOUMNCOUNT_L1","2");
    qDebug() << "w00 = " << getvalue("LAYERCOUNT");
    m_perceptronJsonTerminal.sendJsonBuffer2Engine(getstringbuffer());
}

void PerceptronJsonModel::sltLayerCountUpdate(int layerCount)
{
    qDebug() << "PerceptronJsonModel::sltLayerCountUpdate() = " << layerCount;
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

QString& PerceptronJsonModel::getstringbuffer()
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
