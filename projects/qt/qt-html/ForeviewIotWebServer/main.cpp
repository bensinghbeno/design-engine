/****************************************************************************
**
** Copyright (C) 2014 Kurt Pattyn <pattyn.kurt@gmail.com>.
** Contact: http://www.qt.io/licensing/
**
** This file is part of the QtWebSockets module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:LGPL21$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see http://www.qt.io/terms-conditions. For further
** information use the contact form at http://www.qt.io/contact-us.
**
** GNU Lesser General Public License Usage
** Alternatively, this file may be used under the terms of the GNU Lesser
** General Public License version 2.1 or version 3 as published by the Free
** Software Foundation and appearing in the file LICENSE.LGPLv21 and
** LICENSE.LGPLv3 included in the packaging of this file. Please review the
** following information to ensure the GNU Lesser General Public License
** requirements will be met: https://www.gnu.org/licenses/lgpl.html and
** http://www.gnu.org/licenses/old-licenses/lgpl-2.1.html.
**
** As a special exception, The Qt Company gives you certain additional
** rights. These rights are described in The Qt Company LGPL Exception
** version 1.1, included in the file LGPL_EXCEPTION.txt in this package.
**
** $QT_END_LICENSE$
**
****************************************************************************/
#include <QApplication>
#include <QtCore/QCommandLineParser>
#include <QtCore/QCommandLineOption>
#include "mainwindow.h"
#include "webserver.h"
#include "udpserver.h"

int main(int argc, char *argv[])
{
    QApplication a(argc, argv);

    QCommandLineParser parser;
    parser.setApplicationDescription("QtWebSockets example: echoserver");
    parser.addHelpOption();

    QCommandLineOption dbgOption(QStringList() << "d" << "debug",
            QCoreApplication::translate("main", "Debug output [default: off]."));
    parser.addOption(dbgOption);
    QCommandLineOption portOption(QStringList() << "p" << "port",
            QCoreApplication::translate("main", "Port for echoserver [default: 1234]."),
            QCoreApplication::translate("main", "port"), QLatin1Literal("1234"));
    parser.addOption(portOption);
    parser.process(a);
    bool debug = parser.isSet(dbgOption);
    int port = parser.value(portOption).toInt();

    // Create Logic Model Objects
    WebServer *pWebServer = new WebServer(port, debug);
    MainWindow objMainWindow;
    objMainWindow.show();
    UdpServer objUdpServer;


    // Create Controller Connections
    QObject::connect(pWebServer, &WebServer::closed, &a, &QCoreApplication::quit);
    QObject::connect(&objMainWindow,SIGNAL(sigSendToClient(QString)),pWebServer,SLOT(sendMessage(QString)));
    QObject::connect(pWebServer,SIGNAL(sigMessageRecvFromClient(QString)),&objMainWindow,SLOT(sltUpdateMessageReceived(QString)));
    QObject::connect(&objUdpServer,SIGNAL(sigDatagramReceived(QString)),&objMainWindow,SLOT(sltUpdateUdpMessageReceived(QString)));
    QObject::connect(&objMainWindow,SIGNAL(sigSendToUdpClient(QString)),&objUdpServer,SLOT(sltWriteDatagram(QString)));

    return a.exec();
}
