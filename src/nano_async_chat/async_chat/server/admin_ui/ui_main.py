# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.4.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QLabel, QLineEdit, QPushButton,
    QSizePolicy, QWidget)

class Ui_Form(object):
    def setupUi(self, Form):
        if not Form.objectName():
            Form.setObjectName(u"Form")
        Form.resize(369, 616)
        self.label_5 = QLabel(Form)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(50, 270, 171, 21))
        font = QFont()
        font.setPointSize(12)
        self.label_5.setFont(font)
        self.label_6 = QLabel(Form)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(50, 340, 431, 21))
        self.label_6.setFont(font)
        self.label_7 = QLabel(Form)
        self.label_7.setObjectName(u"label_7")
        self.label_7.setGeometry(QRect(50, 40, 171, 21))
        self.label_7.setFont(font)
        self.label_8 = QLabel(Form)
        self.label_8.setObjectName(u"label_8")
        self.label_8.setGeometry(QRect(50, 110, 171, 21))
        self.label_8.setFont(font)
        self.loginDb = QLineEdit(Form)
        self.loginDb.setObjectName(u"loginDb")
        self.loginDb.setGeometry(QRect(50, 70, 271, 31))
        self.loginDb.setFont(font)
        self.passwordDb = QLineEdit(Form)
        self.passwordDb.setObjectName(u"passwordDb")
        self.passwordDb.setGeometry(QRect(50, 140, 271, 31))
        self.passwordDb.setFont(font)
        self.serverPort = QLineEdit(Form)
        self.serverPort.setObjectName(u"serverPort")
        self.serverPort.setGeometry(QRect(50, 300, 271, 31))
        self.serverPort.setFont(font)
        self.maxUsers = QLineEdit(Form)
        self.maxUsers.setObjectName(u"maxUsers")
        self.maxUsers.setGeometry(QRect(50, 370, 271, 31))
        self.maxUsers.setFont(font)
        self.connectDbStatus = QLabel(Form)
        self.connectDbStatus.setObjectName(u"connectDbStatus")
        self.connectDbStatus.setGeometry(QRect(50, 180, 271, 31))
        self.connectDbStatus.setFont(font)
        self.connectDbStatus.setLayoutDirection(Qt.RightToLeft)
        self.connectDbStatus.setAlignment(Qt.AlignCenter)
        self.connectDbStatus.setMargin(0)
        self.connectDbStatus.setIndent(0)
        self.startServer = QPushButton(Form)
        self.startServer.setObjectName(u"startServer")
        self.startServer.setGeometry(QRect(50, 410, 271, 41))
        self.startServer.setFont(font)
        self.showUserListStat = QPushButton(Form)
        self.showUserListStat.setObjectName(u"showUserListStat")
        self.showUserListStat.setGeometry(QRect(120, 560, 131, 41))
        self.showUserListStat.setFont(font)
        self.showUserList = QPushButton(Form)
        self.showUserList.setObjectName(u"showUserList")
        self.showUserList.setGeometry(QRect(120, 500, 131, 41))
        self.showUserList.setFont(font)
        self.serverStatus = QLabel(Form)
        self.serverStatus.setObjectName(u"serverStatus")
        self.serverStatus.setGeometry(QRect(50, 460, 271, 20))
        self.serverStatus.setFont(font)
        self.serverStatus.setAlignment(Qt.AlignCenter)

        self.retranslateUi(Form)

        QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QCoreApplication.translate("Form", u"Form", None))
        self.label_5.setText(QCoreApplication.translate("Form", u"\u041f\u043e\u0440\u0442", None))
        self.label_6.setText(QCoreApplication.translate("Form", u"\u041c\u0430\u043a\u0441\u0438\u043c\u0443\u043c \u0441\u043b\u0443\u0448\u0430\u0435\u043c\u044b\u0445 \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u0439", None))
        self.label_7.setText(QCoreApplication.translate("Form", u"\u041b\u043e\u0433\u0438\u043d \u0411\u0414", None))
        self.label_8.setText(QCoreApplication.translate("Form", u"\u041f\u0430\u0440\u043e\u043b\u044c \u0411\u0414", None))
        self.loginDb.setText(QCoreApplication.translate("Form", u"123", None))
        self.passwordDb.setText(QCoreApplication.translate("Form", u"123", None))
        self.serverPort.setText(QCoreApplication.translate("Form", u"123", None))
        self.maxUsers.setText(QCoreApplication.translate("Form", u"123", None))
        self.connectDbStatus.setText(QCoreApplication.translate("Form", u"no connect", None))
        self.startServer.setText(QCoreApplication.translate("Form", u"\u0421\u0442\u0430\u0440\u0442 \u0441\u0435\u0440\u0432\u0435\u0440\u0430", None))
        self.showUserListStat.setText(QCoreApplication.translate("Form", u"\u0421\u0442\u0430\u0442\u0438\u0441\u0442\u0438\u043a\u0430", None))
        self.showUserList.setText(QCoreApplication.translate("Form", u"\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438", None))
        self.serverStatus.setText(QCoreApplication.translate("Form", u"no start", None))
    # retranslateUi

