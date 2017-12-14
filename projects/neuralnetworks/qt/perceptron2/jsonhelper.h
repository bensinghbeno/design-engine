#ifndef JSONLOAD_H
#define JSONLOAD_H

#include <QFile>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QByteArray>
#include <QJsonValue>

class JsonHelper : public QObject
{
public:
    JsonHelper();
    void readJson(QString filepath);
    void loadjsonfile(QString filepath);
    void insertvalue(QString key, QString value);
    QString getvalue(QString key);
    QString& getstringbuffer();
    void insertJsonStringbuffer(QString strJson);

    void demo();

    QFile m_file;
    QString m_fileBuffer;
    QString m_stringbuffer;
    QJsonDocument m_docjson;

    QJsonValue m_valweight;
    QJsonObject m_objlayer;
    QString m_strdocjson;
};

#endif // JSONLOAD_H
