/*
 * This file was generated by qdbusxml2cpp version 0.8
 * Command line was: qdbusxml2cpp -v -c clientIf -p clientIf.h:clientIf.cpp ../dbus-server/com.dbus.example.interface.xml
 *
 * qdbusxml2cpp is Copyright (C) 2016 The Qt Company Ltd.
 *
 * This is an auto-generated file.
 * Do not edit! All changes made to it will be lost.
 */

#ifndef CLIENTIF_H
#define CLIENTIF_H

#include <QtCore/QObject>
#include <QtCore/QByteArray>
#include <QtCore/QList>
#include <QtCore/QMap>
#include <QtCore/QString>
#include <QtCore/QStringList>
#include <QtCore/QVariant>
#include <QtDBus/QtDBus>

/*
 * Proxy class for interface local.interfacedescription
 */
class clientIf: public QDBusAbstractInterface
{
    Q_OBJECT
public:
    static inline const char *staticInterfaceName()
    { return "local.interfacedescription"; }

public:
    clientIf(const QString &service, const QString &path, const QDBusConnection &connection, QObject *parent = 0);

    ~clientIf();

public Q_SLOTS: // METHODS
    inline QDBusPendingReply<> RequestBroadcastSignal(const QString &aMessage)
    {
        QList<QVariant> argumentList;
        argumentList << QVariant::fromValue(aMessage);
        return asyncCallWithArgumentList(QStringLiteral("RequestBroadcastSignal"), argumentList);
    }

    inline QDBusPendingReply<> sendCommand(const QString &aCommand)
    {
        QList<QVariant> argumentList;
        argumentList << QVariant::fromValue(aCommand);
        return asyncCallWithArgumentList(QStringLiteral("sendCommand"), argumentList);
    }

Q_SIGNALS: // SIGNALS
    void BroadcastCommandSignal(const QString &aCommandMessage);
};

namespace local {
  typedef ::clientIf interfacedescription;
}
#endif