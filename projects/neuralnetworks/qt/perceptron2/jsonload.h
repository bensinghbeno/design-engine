#ifndef JSONLOAD_H
#define JSONLOAD_H

#include <QFile>
#include <QJsonObject>
#include <QJsonDocument>
#include <QJsonArray>
#include <QByteArray>

class JsonLoad
{
public:
    JsonLoad();
    void readJson(QString filepath);
    void loadjsonfile(QString filepath);

    QFile m_file;
    QString m_fileBuffer;


};

#endif // JSONLOAD_H
