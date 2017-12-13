#include "jsonhelper.h"
#include <QDebug>
#include <QByteArray>

JsonHelper::JsonHelper()
{

}

void JsonHelper::insertvalue(QString key, QString value)
{

    m_valweight = value;
    m_objlayer.insert(key,m_valweight);

}

QString JsonHelper::getvalue(QString key)
{
    return m_objlayer.value(key).toString();
}

QString& JsonHelper::getstringbuffer()
{

    m_docjson.setObject(m_objlayer);
    m_strdocjson =  m_docjson.toJson();
    return m_strdocjson;
}

void JsonHelper::insertJsonStringbuffer(QString strJson)
{
    m_docjson = QJsonDocument::fromJson(strJson.toUtf8());
    m_objlayer = m_docjson.object();
}

void JsonHelper::loadjsonfile(QString filepath)
{
    m_file.setFileName(filepath);
    m_file.open(QIODevice::ReadOnly | QIODevice::Text);
    m_fileBuffer = m_file.readAll();
    m_file.close();

}

void JsonHelper::readJson(QString filepath)
{
    loadjsonfile(filepath);
    //qWarning() << val;

    QJsonDocument jsondoc = QJsonDocument::fromJson(m_fileBuffer.toUtf8());
    QJsonObject sett = jsondoc.object();
    QJsonValue value = sett.value(QString("appName"));
    QJsonObject item = value.toObject();
    QJsonArray test = item["layer1"].toArray();
    //qDebug() << "orig = " << test[2].toString();



    QString buff2 =  jsondoc.toJson();
    QJsonDocument jsondoc2 = QJsonDocument::fromJson(buff2.toUtf8());
    QJsonObject sett2 = jsondoc2.object();
    QJsonValue value2 = sett2.value(QString("appName"));
    QJsonObject item2 = value2.toObject();
    QJsonArray test2 = item2["layer1"].toArray();
    //qDebug() << "orig2 = " << test2[2].toString();
}

void JsonHelper::demo()
{
    insertvalue("w00","1677");
    insertvalue("w01","19");
    insertvalue("w00","77");
    qDebug() << "json string buffer = " << getstringbuffer();

    insertvalue("w01","55");
    insertJsonStringbuffer(getstringbuffer());


    qDebug() << "w00 = " << getvalue("w00");
    qDebug() << "w01 = " << getvalue("w01");
}

