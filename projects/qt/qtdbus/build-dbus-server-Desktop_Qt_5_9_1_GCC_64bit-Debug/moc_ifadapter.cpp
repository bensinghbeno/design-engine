/****************************************************************************
** Meta object code from reading C++ file 'ifadapter.h'
**
** Created by: The Qt Meta Object Compiler version 67 (Qt 5.9.1)
**
** WARNING! All changes made in this file will be lost!
*****************************************************************************/

#include "../dbus-server/ifadapter.h"
#include <QtCore/qbytearray.h>
#include <QtCore/qmetatype.h>
#if !defined(Q_MOC_OUTPUT_REVISION)
#error "The header file 'ifadapter.h' doesn't include <QObject>."
#elif Q_MOC_OUTPUT_REVISION != 67
#error "This file was generated using the moc from 5.9.1. It"
#error "cannot be used with the include files from this version of Qt."
#error "(The moc has changed too much.)"
#endif

QT_BEGIN_MOC_NAMESPACE
QT_WARNING_PUSH
QT_WARNING_DISABLE_DEPRECATED
struct qt_meta_stringdata_ifadapter_t {
    QByteArrayData data[12];
    char stringdata0[644];
};
#define QT_MOC_LITERAL(idx, ofs, len) \
    Q_STATIC_BYTE_ARRAY_DATA_HEADER_INITIALIZER_WITH_OFFSET(len, \
    qptrdiff(offsetof(qt_meta_stringdata_ifadapter_t, stringdata0) + ofs \
        - idx * sizeof(QByteArrayData)) \
    )
static const qt_meta_stringdata_ifadapter_t qt_meta_stringdata_ifadapter = {
    {
QT_MOC_LITERAL(0, 0, 9), // "ifadapter"
QT_MOC_LITERAL(1, 10, 15), // "D-Bus Interface"
QT_MOC_LITERAL(2, 26, 26), // "local.interfacedescription"
QT_MOC_LITERAL(3, 53, 19), // "D-Bus Introspection"
QT_MOC_LITERAL(4, 73, 510), // "  <interface name=\"local.int..."
QT_MOC_LITERAL(5, 535, 17), // "somethingHappened"
QT_MOC_LITERAL(6, 553, 0), // ""
QT_MOC_LITERAL(7, 554, 13), // "signalMessage"
QT_MOC_LITERAL(8, 568, 11), // "SendMessage"
QT_MOC_LITERAL(9, 580, 3), // "cmd"
QT_MOC_LITERAL(10, 584, 4), // "read"
QT_MOC_LITERAL(11, 589, 5) // "write"

    },
    "ifadapter\0D-Bus Interface\0"
    "local.interfacedescription\0"
    "D-Bus Introspection\0"
    "  <interface name=\"local.interfacedescription\">\n    <signal name=\""
    "somethingHappened\">\n      <arg direction=\"out\" type=\"s\" name=\"s"
    "ignalMessage\"/>\n    </signal>\n    <method name=\"read\">\n      <ar"
    "g direction=\"out\" type=\"s\"/>\n    </method>\n    <method name=\"wr"
    "ite\">\n      <arg direction=\"out\" type=\"s\"/>\n    </method>\n    "
    "<method name=\"SendMessage\">\n      <arg direction=\"out\" type=\"s\""
    "/>\n      <arg direction=\"in\" type=\"s\" name=\"cmd\"/>\n    </metho"
    "d>\n  </interface>\n\0"
    "somethingHappened\0\0signalMessage\0"
    "SendMessage\0cmd\0read\0write"
};
#undef QT_MOC_LITERAL

static const uint qt_meta_data_ifadapter[] = {

 // content:
       7,       // revision
       0,       // classname
       2,   14, // classinfo
       4,   18, // methods
       0,    0, // properties
       0,    0, // enums/sets
       0,    0, // constructors
       0,       // flags
       1,       // signalCount

 // classinfo: key, value
       1,    2,
       3,    4,

 // signals: name, argc, parameters, tag, flags
       5,    1,   38,    6, 0x06 /* Public */,

 // slots: name, argc, parameters, tag, flags
       8,    1,   41,    6, 0x0a /* Public */,
      10,    0,   44,    6, 0x0a /* Public */,
      11,    0,   45,    6, 0x0a /* Public */,

 // signals: parameters
    QMetaType::Void, QMetaType::QString,    7,

 // slots: parameters
    QMetaType::QString, QMetaType::QString,    9,
    QMetaType::QString,
    QMetaType::QString,

       0        // eod
};

void ifadapter::qt_static_metacall(QObject *_o, QMetaObject::Call _c, int _id, void **_a)
{
    if (_c == QMetaObject::InvokeMetaMethod) {
        ifadapter *_t = static_cast<ifadapter *>(_o);
        Q_UNUSED(_t)
        switch (_id) {
        case 0: _t->somethingHappened((*reinterpret_cast< const QString(*)>(_a[1]))); break;
        case 1: { QString _r = _t->SendMessage((*reinterpret_cast< const QString(*)>(_a[1])));
            if (_a[0]) *reinterpret_cast< QString*>(_a[0]) = std::move(_r); }  break;
        case 2: { QString _r = _t->read();
            if (_a[0]) *reinterpret_cast< QString*>(_a[0]) = std::move(_r); }  break;
        case 3: { QString _r = _t->write();
            if (_a[0]) *reinterpret_cast< QString*>(_a[0]) = std::move(_r); }  break;
        default: ;
        }
    } else if (_c == QMetaObject::IndexOfMethod) {
        int *result = reinterpret_cast<int *>(_a[0]);
        void **func = reinterpret_cast<void **>(_a[1]);
        {
            typedef void (ifadapter::*_t)(const QString & );
            if (*reinterpret_cast<_t *>(func) == static_cast<_t>(&ifadapter::somethingHappened)) {
                *result = 0;
                return;
            }
        }
    }
}

const QMetaObject ifadapter::staticMetaObject = {
    { &QDBusAbstractAdaptor::staticMetaObject, qt_meta_stringdata_ifadapter.data,
      qt_meta_data_ifadapter,  qt_static_metacall, nullptr, nullptr}
};


const QMetaObject *ifadapter::metaObject() const
{
    return QObject::d_ptr->metaObject ? QObject::d_ptr->dynamicMetaObject() : &staticMetaObject;
}

void *ifadapter::qt_metacast(const char *_clname)
{
    if (!_clname) return nullptr;
    if (!strcmp(_clname, qt_meta_stringdata_ifadapter.stringdata0))
        return static_cast<void*>(const_cast< ifadapter*>(this));
    return QDBusAbstractAdaptor::qt_metacast(_clname);
}

int ifadapter::qt_metacall(QMetaObject::Call _c, int _id, void **_a)
{
    _id = QDBusAbstractAdaptor::qt_metacall(_c, _id, _a);
    if (_id < 0)
        return _id;
    if (_c == QMetaObject::InvokeMetaMethod) {
        if (_id < 4)
            qt_static_metacall(this, _c, _id, _a);
        _id -= 4;
    } else if (_c == QMetaObject::RegisterMethodArgumentMetaType) {
        if (_id < 4)
            *reinterpret_cast<int*>(_a[0]) = -1;
        _id -= 4;
    }
    return _id;
}

// SIGNAL 0
void ifadapter::somethingHappened(const QString & _t1)
{
    void *_a[] = { nullptr, const_cast<void*>(reinterpret_cast<const void*>(&_t1)) };
    QMetaObject::activate(this, &staticMetaObject, 0, _a);
}
QT_WARNING_POP
QT_END_MOC_NAMESPACE
