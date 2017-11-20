#ifndef JSONLOAD_H
#define JSONLOAD_H

#include <QFile>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QByteArray>
#include <QJsonValue>

class JsonLoad
{
public:
    JsonLoad();
    void readJson(QString filepath);
    void loadjsonfile(QString filepath);
    void insertvalue(QString key, QString value);
    QString getvalue(QString key);

    QFile m_file;
    QString m_fileBuffer;

    QJsonValue m_valweight;
    QJsonObject m_objlayer;
    QJsonDocument m_docjson;
    QString m_strdocjson;
};

#endif // JSONLOAD_H
