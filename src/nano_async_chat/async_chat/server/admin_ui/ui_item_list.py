# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'item_list.ui'
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
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QHeaderView,
    QLabel, QPushButton, QSizePolicy, QTableWidget,
    QTableWidgetItem, QWidget)

class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(930, 628)
        self.itemList = QTableWidget(Dialog)
        if (self.itemList.columnCount() < 1):
            self.itemList.setColumnCount(1)
        __qtablewidgetitem = QTableWidgetItem()
        self.itemList.setHorizontalHeaderItem(0, __qtablewidgetitem)
        if (self.itemList.rowCount() < 1):
            self.itemList.setRowCount(1)
        __qtablewidgetitem1 = QTableWidgetItem()
        self.itemList.setVerticalHeaderItem(0, __qtablewidgetitem1)
        self.itemList.setObjectName(u"itemList")
        self.itemList.setGeometry(QRect(10, 80, 891, 441))
        self.previousPage = QPushButton(Dialog)
        self.previousPage.setObjectName(u"previousPage")
        self.previousPage.setGeometry(QRect(320, 530, 91, 41))
        self.nextPage = QPushButton(Dialog)
        self.nextPage.setObjectName(u"nextPage")
        self.nextPage.setGeometry(QRect(420, 530, 91, 41))
        self.title = QLabel(Dialog)
        self.title.setObjectName(u"title")
        self.title.setGeometry(QRect(350, 30, 191, 41))
        font = QFont()
        font.setPointSize(20)
        self.title.setFont(font)
        self.onlyOnline = QCheckBox(Dialog)
        self.onlyOnline.setObjectName(u"onlyOnline")
        self.onlyOnline.setGeometry(QRect(40, 530, 101, 31))
        self.pageNum = QLabel(Dialog)
        self.pageNum.setObjectName(u"pageNum")
        self.pageNum.setGeometry(QRect(290, 540, 47, 21))
        font1 = QFont()
        font1.setPointSize(15)
        self.pageNum.setFont(font1)

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Dialog", None))
        ___qtablewidgetitem = self.itemList.horizontalHeaderItem(0)
        ___qtablewidgetitem.setText(QCoreApplication.translate("Dialog", u"123", None));
        ___qtablewidgetitem1 = self.itemList.verticalHeaderItem(0)
        ___qtablewidgetitem1.setText(QCoreApplication.translate("Dialog", u"456", None));
        self.previousPage.setText(QCoreApplication.translate("Dialog", u"\u041f\u0440\u0435\u0434\u044b\u0434\u0443\u0449\u0430\u044f", None))
        self.nextPage.setText(QCoreApplication.translate("Dialog", u"\u0421\u043b\u0435\u0434\u0443\u044e\u0449\u0430\u044f", None))
        self.title.setText(QCoreApplication.translate("Dialog", u"\u041f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0438", None))
        self.onlyOnline.setText(QCoreApplication.translate("Dialog", u"\u0442\u043e\u043b\u044c\u043a\u043e online", None))
        self.pageNum.setText(QCoreApplication.translate("Dialog", u"1", None))
    # retranslateUi

