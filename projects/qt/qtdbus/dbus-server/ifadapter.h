/*
 * This file was generated by qdbusxml2cpp version 0.8
 * Command line was: qdbusxml2cpp -c ifadapter -a ifadapter.h:ifadapter.cpp com.dbus.example.interface.xml
 *
 * qdbusxml2cpp is Copyright (C) 2016 The Qt Company Ltd.
 *
 * This is an auto-generated file.
 * This file may have been hand-edited. Look for HAND-EDIT comments
 * before re-generating it.
 */

#ifndef IFADAPTER_H
#define IFADAPTER_H

#include <QtCore/QObject>
#include <QtDBus/QtDBus>
QT_BEGIN_NAMESPACE
class QByteArray;
template<class T> class QList;
template<class Key, class Value> class QMap;
class QString;
class QStringList;
class QVariant;
QT_END_NAMESPACE

/*
 * Adaptor class for interface local.interfacedescription
 */
class ifadapter: public QDBusAbstractAdaptor
{
    Q_OBJECT
    Q_CLASSINFO("D-Bus Interface", "local.interfacedescription")
    Q_CLASSINFO("D-Bus Introspection", ""
"  <interface name=\"local.interfacedescription\">\n"
"    <signal name=\"BroadcastCommandSignal\">\n"
"      <arg direction=\"out\" type=\"s\" name=\"aCommandMessage\"/>\n"
"    </signal>\n"
"    <method name=\"sendCommand\">\n"
"      <arg direction=\"in\" type=\"s\" name=\"aCommand\"/>\n"
"    </method>\n"
"    <method name=\"RequestBroadcastSignal\">\n"
"      <arg direction=\"in\" type=\"s\" name=\"aMessage\"/>\n"
"    </method>\n"
"  </interface>\n"
        "")
public:
    ifadapter(QObject *parent);
    virtual ~ifadapter();

public: // PROPERTIES
public Q_SLOTS: // METHODS
    void RequestBroadcastSignal(const QString &aMessage);
    void sendCommand(const QString &aCommand);
Q_SIGNALS: // SIGNALS
    void BroadcastCommandSignal(const QString &aCommandMessage);
};

#endif
