# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'client.ui'
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
from PySide6.QtWidgets import (QApplication, QDialog, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton,
    QSizePolicy, QTextBrowser, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(766, 780)
        self.loginLine = QLineEdit(Dialog)
        self.loginLine.setObjectName(u"loginLine")
        self.loginLine.setGeometry(QRect(420, 620, 141, 31))
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(12)
        self.loginLine.setFont(font)
        self.label = QLabel(Dialog)
        self.label.setObjectName(u"label")
        self.label.setGeometry(QRect(420, 600, 81, 21))
        self.label.setFont(font)
        self.passwordLine = QLineEdit(Dialog)
        self.passwordLine.setObjectName(u"passwordLine")
        self.passwordLine.setGeometry(QRect(420, 679, 141, 31))
        self.passwordLine.setFont(font)
        self.label_2 = QLabel(Dialog)
        self.label_2.setObjectName(u"label_2")
        self.label_2.setGeometry(QRect(420, 660, 91, 21))
        self.label_2.setFont(font)
        self.ipLine = QLineEdit(Dialog)
        self.ipLine.setObjectName(u"ipLine")
        self.ipLine.setGeometry(QRect(250, 620, 141, 31))
        self.ipLine.setFont(font)
        self.label_3 = QLabel(Dialog)
        self.label_3.setObjectName(u"label_3")
        self.label_3.setGeometry(QRect(250, 600, 51, 21))
        self.label_3.setFont(font)
        self.portLine = QLineEdit(Dialog)
        self.portLine.setObjectName(u"portLine")
        self.portLine.setGeometry(QRect(250, 679, 141, 31))
        self.portLine.setFont(font)
        self.label_4 = QLabel(Dialog)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(250, 660, 51, 21))
        self.label_4.setFont(font)
        self.connectButton = QPushButton(Dialog)
        self.connectButton.setObjectName(u"connectButton")
        self.connectButton.setGeometry(QRect(250, 720, 141, 41))
        self.connectButton.setFont(font)
        self.onlineStatus = QLabel(Dialog)
        self.onlineStatus.setObjectName(u"onlineStatus")
        self.onlineStatus.setGeometry(QRect(270, 560, 101, 51))
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(16)
        self.onlineStatus.setFont(font1)
        self.onlineStatus.setAlignment(Qt.AlignCenter)
        self.roomNameHeader = QLabel(Dialog)
        self.roomNameHeader.setObjectName(u"roomNameHeader")
        self.roomNameHeader.setGeometry(QRect(40, 20, 121, 41))
        font2 = QFont()
        font2.setFamilies([u"Arial"])
        font2.setPointSize(20)
        self.roomNameHeader.setFont(font2)
        self.sendMessageButton = QPushButton(Dialog)
        self.sendMessageButton.setObjectName(u"sendMessageButton")
        self.sendMessageButton.setGeometry(QRect(40, 500, 141, 41))
        self.sendMessageButton.setFont(font)
        self.contactsList = QListWidget(Dialog)
        self.contactsList.setObjectName(u"contactsList")
        self.contactsList.setGeometry(QRect(530, 60, 201, 381))
        font3 = QFont()
        font3.setFamilies([u"Arial"])
        font3.setPointSize(14)
        self.contactsList.setFont(font3)
        self.onlineOffline_3 = QLabel(Dialog)
        self.onlineOffline_3.setObjectName(u"onlineOffline_3")
        self.onlineOffline_3.setGeometry(QRect(540, 20, 221, 41))
        font4 = QFont()
        font4.setFamilies([u"Arial"])
        font4.setPointSize(18)
        self.onlineOffline_3.setFont(font4)
        self.messageField = QPlainTextEdit(Dialog)
        self.messageField.setObjectName(u"messageField")
        self.messageField.setGeometry(QRect(40, 450, 471, 41))
        font5 = QFont()
        font5.setFamilies([u"Consolas"])
        font5.setPointSize(12)
        self.messageField.setFont(font5)
        self.roomNameLine = QLineEdit(Dialog)
        self.roomNameLine.setObjectName(u"roomNameLine")
        self.roomNameLine.setGeometry(QRect(40, 679, 141, 31))
        self.roomNameLine.setFont(font)
        self.label_5 = QLabel(Dialog)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setGeometry(QRect(40, 660, 71, 21))
        self.label_5.setFont(font)
        self.enterRoomButton = QPushButton(Dialog)
        self.enterRoomButton.setObjectName(u"enterRoomButton")
        self.enterRoomButton.setGeometry(QRect(40, 720, 141, 41))
        self.enterRoomButton.setFont(font)
        self.logoutButton = QPushButton(Dialog)
        self.logoutButton.setObjectName(u"logoutButton")
        self.logoutButton.setGeometry(QRect(580, 720, 141, 41))
        self.logoutButton.setFont(font)
        self.loginStatus = QLabel(Dialog)
        self.loginStatus.setObjectName(u"loginStatus")
        self.loginStatus.setGeometry(QRect(410, 560, 161, 51))
        self.loginStatus.setFont(font3)
        self.loginStatus.setAlignment(Qt.AlignCenter)
        self.leaveRoomButton = QPushButton(Dialog)
        self.leaveRoomButton.setObjectName(u"leaveRoomButton")
        self.leaveRoomButton.setGeometry(QRect(190, 500, 321, 41))
        self.leaveRoomButton.setFont(font)
        self.contactNameLine = QLineEdit(Dialog)
        self.contactNameLine.setObjectName(u"contactNameLine")
        self.contactNameLine.setGeometry(QRect(40, 569, 141, 31))
        self.contactNameLine.setFont(font)
        self.addContactButton = QPushButton(Dialog)
        self.addContactButton.setObjectName(u"addContactButton")
        self.addContactButton.setGeometry(QRect(40, 610, 141, 41))
        self.addContactButton.setFont(font)
        self.deleteContactButton = QPushButton(Dialog)
        self.deleteContactButton.setObjectName(u"deleteContactButton")
        self.deleteContactButton.setGeometry(QRect(530, 450, 201, 41))
        self.deleteContactButton.setFont(font)
        self.label_6 = QLabel(Dialog)
        self.label_6.setObjectName(u"label_6")
        self.label_6.setGeometry(QRect(40, 550, 151, 21))
        self.label_6.setFont(font)
        self.roomChat = QTextBrowser(Dialog)
        self.roomChat.setObjectName(u"roomChat")
        self.roomChat.setEnabled(True)
        self.roomChat.setGeometry(QRect(40, 61, 471, 371))
        self.roomChat.setFont(font5)
        self.roomChat.setLayoutDirection(Qt.LeftToRight)
        self.roomChat.setAutoFillBackground(False)
        self.roomChat.setOverwriteMode(False)
        self.loginButton = QPushButton(Dialog)
        self.loginButton.setObjectName(u"loginButton")
        self.loginButton.setGeometry(QRect(420, 720, 141, 41))
        self.loginButton.setFont(font)
        self.roomName = QLabel(Dialog)
        self.roomName.setObjectName(u"roomName")
        self.roomName.setGeometry(QRect(160, 20, 121, 41))
        self.roomName.setFont(font2)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        self.label.setText(QCoreApplication.translate("Dialog", u"login", None))
        self.label_2.setText(QCoreApplication.translate("Dialog", u"password", None))
        self.ipLine.setText("")
        self.label_3.setText(QCoreApplication.translate("Dialog", u"\u0410\u0434\u0440\u0435\u0441", None))
        self.label_4.setText(QCoreApplication.translate("Dialog", u"\u041f\u043e\u0440\u0442", None))
        self.connectButton.setText(QCoreApplication.translate("Dialog", u"\u041f\u043e\u0434\u043a\u043b\u044e\u0447\u0438\u0442\u044c\u0441\u044f", None))
        self.onlineStatus.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p><span style=\" color:#ff5500;\">offline</span></p></body></html>", None))
        self.roomNameHeader.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>\u041a\u043e\u043c\u043d\u0430\u0442\u0430:</p></body></html>", None))
        self.sendMessageButton.setText(QCoreApplication.translate("Dialog", u"\u041e\u0442\u043e\u0441\u043b\u0430\u0442\u044c", None))
        self.onlineOffline_3.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>\u0421\u043f\u0438\u0441\u043e\u043a \u0434\u0440\u0443\u0437\u0435\u0439</p></body></html>", None))
        self.label_5.setText(QCoreApplication.translate("Dialog", u"\u041a\u043e\u043c\u043d\u0430\u0442\u0430", None))
        self.enterRoomButton.setText(QCoreApplication.translate("Dialog", u"\u041f\u0440\u0438\u0441\u043e\u0435\u0434\u0438\u043d\u0438\u0442\u044c\u0441\u044f", None))
        self.logoutButton.setText(QCoreApplication.translate("Dialog", u"\u0420\u0430\u0437\u043b\u043e\u0433\u0438\u043d\u0438\u0442\u044c\u0441\u044f", None))
        self.loginStatus.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>\u041d\u0435 \u0430\u0432\u0442\u043e\u0440\u0438\u0437\u043e\u0432\u0430\u043d</p></body></html>", None))
        self.leaveRoomButton.setText(QCoreApplication.translate("Dialog", u"\u0412\u044b\u0439\u0442\u0438 \u0438\u0437 \u043a\u043e\u043c\u043d\u0430\u0442\u044b \u0438 \u0432\u043e\u0439\u0442\u0438 \u0432 \u043e\u0431\u0449\u0443\u044e", None))
        self.addContactButton.setText(QCoreApplication.translate("Dialog", u"\u0414\u043e\u0431\u0430\u0432\u0438\u0442\u044c \u0434\u0440\u0443\u0433\u0430", None))
        self.deleteContactButton.setText(QCoreApplication.translate("Dialog", u"\u0423\u0434\u0430\u043b\u0438\u0442\u044c \u0434\u0440\u0443\u0433\u0430", None))
        self.label_6.setText(QCoreApplication.translate("Dialog", u"\u041b\u043e\u0433\u0438\u043d \u043a\u043e\u043d\u0442\u0430\u043a\u0442\u0430", None))
#if QT_CONFIG(tooltip)
        self.roomChat.setToolTip("")
#endif // QT_CONFIG(tooltip)
        self.roomChat.setHtml(QCoreApplication.translate("Dialog", u"<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:'Consolas'; font-size:12pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:'MS Shell Dlg 2';\"><br /></p></body></html>", None))
        self.loginButton.setText(QCoreApplication.translate("Dialog", u"\u0410\u0432\u0442\u043e\u0440\u0438\u0437\u0430\u0446\u0438\u044f", None))
        self.roomName.setText(QCoreApplication.translate("Dialog", u"<html><head/><body><p>x</p></body></html>", None))
    # retranslateUi

