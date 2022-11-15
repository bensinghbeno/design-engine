/****************************************************************************
**
** Copyright (C) 2013 Laszlo Papp <lpapp@kde.org>
** Contact: https://www.qt.io/licensing/
**
** This file is part of the QtSerialPort module of the Qt Toolkit.
**
** $QT_BEGIN_LICENSE:BSD$
** Commercial License Usage
** Licensees holding valid commercial Qt licenses may use this file in
** accordance with the commercial license agreement provided with the
** Software or, alternatively, in accordance with the terms contained in
** a written agreement between you and The Qt Company. For licensing terms
** and conditions see https://www.qt.io/terms-conditions. For further
** information use the contact form at https://www.qt.io/contact-us.
**
** BSD License Usage
** Alternatively, you may use this file under the terms of the BSD license
** as follows:
**
** "Redistribution and use in source and binary forms, with or without
** modification, are permitted provided that the following conditions are
** met:
**   * Redistributions of source code must retain the above copyright
**     notice, this list of conditions and the following disclaimer.
**   * Redistributions in binary form must reproduce the above copyright
**     notice, this list of conditions and the following disclaimer in
**     the documentation and/or other materials provided with the
**     distribution.
**   * Neither the name of The Qt Company Ltd nor the names of its
**     contributors may be used to endorse or promote products derived
**     from this software without specific prior written permission.
**
**
** THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
** "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
** LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
** A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
** OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
** SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
** LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
** DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
** THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
** (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
** OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
**
** $QT_END_LICENSE$
**
****************************************************************************/

#include "serialportreader.h"

#include <QCoreApplication>
#include <QDebug>

QT_USE_NAMESPACE

SerialPortReader::SerialPortReader(QString serialPortName, QObject *parent)
    : QObject(parent)
    , mSerialPortName(serialPortName)
    , m_standardOutput(stdout)
{
    qDebug("SerialPortReader::SerialPortReader()");
}

void SerialPortReader::process()
{
    qDebug() << "SerialPortReader Thread::Process()";

    m_timer = new QTimer();

    mSerial = new QSerialPort;
    //QString mSerialPortName = "ttyUSB0";
    mSerial->setPortName(mSerialPortName);
    int serialPortBaudRate = QSerialPort::Baud115200;
    mSerial->setBaudRate(serialPortBaudRate);

    if (!mSerial->open(QIODevice::ReadOnly))
    {
        qDebug() << "Failed to open port : " << mSerialPortName << "Error : " << mSerial->errorString();

        QCoreApplication::quit();
    }

    connect(mSerial, &QSerialPort::readyRead, this, &SerialPortReader::handleReadyRead);
    connect(mSerial, static_cast<void (QSerialPort::*)(QSerialPort::SerialPortError)>(&QSerialPort::error),
            this, &SerialPortReader::handleError);
    connect(m_timer, &QTimer::timeout, this, &SerialPortReader::handleTimeout);

    m_timer->start(10);
}

SerialPortReader::~SerialPortReader()
{
    qDebug("SerialPortReader::~SerialPortReader()");

}

void SerialPortReader::handleReadyRead()
{
    m_standardOutput << QObject::tr("SerialPortReader::handleReadyRead") << endl;

    m_readData.append(mSerial->readAll());

    if (!m_timer->isActive())
        m_timer->start(1);
}

void SerialPortReader::handleTimeout()
{
    if (m_readData.isEmpty())
    {
        qDebug() << "No data was currently available for reading from port : " << mSerial->portName();
    }
    else
    {
        qDebug() << "Data successfully received from port : " << mSerial->portName() << endl   ;
        qDebug()  << m_readData << endl;

        QString str(m_readData);
        if (str.size() > 45)
        {
            QString last = str.right(45);
            QStringList list1 = last.split("Range:");
            if (!list1.empty())
            {
                QStringList list2 = list1.at(1).split("m\t");

                if (!list2.empty())
                {
                    QString range = list2.at(0);
                    //qDebug()  << endl << "===== RANGE 0 = " << range << endl;
                    emit updateData(range);
                }
            }
        }



    }
    m_readData.clear();


    //QCoreApplication::quit();
}

void SerialPortReader::handleError(QSerialPort::SerialPortError serialPortError)
{
    if (serialPortError == QSerialPort::ReadError) {
        m_standardOutput << QObject::tr("An I/O error occurred while reading the data from port %1, error: %2").arg(mSerial->portName()).arg(mSerial->errorString()) << endl;
        QCoreApplication::exit(1);
    }
}
