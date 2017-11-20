#include "jsonload.h"
#include <QDebug>
#include <QByteArray>

JsonLoad::JsonLoad()
{



}

void JsonLoad::loadjsonfile(QString filepath)
{
    m_file.setFileName(filepath);
    m_file.open(QIODevice::ReadOnly | QIODevice::Text);
    m_fileBuffer = m_file.readAll();
    m_file.close();

}

void JsonLoad::readJson(QString filepath)
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



      QJsonValue valweight("16");
      QJsonObject objlayer;
      objlayer.insert("w00",valweight);
      valweight = "17";
      objlayer.insert("w01",valweight);
      qDebug() << "w00 = " << objlayer.value("w00").toString();
      qDebug() << "w01 = " << objlayer.value("w01").toString();
      QJsonDocument docjson;
      docjson.setObject(objlayer);


      QString strdocjson =  docjson.toJson();
      QJsonDocument docjson2 = QJsonDocument::fromJson(strdocjson.toUtf8());
      QJsonObject objlayer2 = docjson2.object();
      qDebug() << "w00 = " << objlayer2.value("w00").toString();
      qDebug() << "w01 = " << objlayer2.value("w01").toString();


}
