import sys
from pathlib import Path
from PySide6 import QtWidgets, QtCore, QtUiTools
from async_chat.server.admin_ui.paginator import Paginator


class ItemList:
    colums = [
        {
            'label': '',
            'field_name': '',
            'width': 200
        }
    ]
    title = ''
    ui_path = Path(__file__).resolve().parent / 'item_list.ui'

    def __init__(
        self,
        parent: QtWidgets.QWidget,
        page_size: int = 5,
        title: str = ''
    ):
        self.page_size = page_size
        self.parent = parent

        self.itemTableWidget: QtWidgets.QTableWidget = parent.itemList
        self.itemTableWidget.setEditTriggers(
            QtWidgets.QTableWidget.NoEditTriggers
        )
        self.pageNumLabel: QtWidgets.QLabel = parent.pageNum
        self.nextPageButton: QtWidgets.QPushButton = parent.nextPage
        self.previousPageButton: QtWidgets.QPushButton = parent.previousPage
        self.onlyOnlineButton: QtWidgets.QCheckBox = parent.onlyOnline
        self.titleLabel: QtWidgets.QLabel = parent.title
        self.titleLabel.setText(title)

        self.nextPageButton.clicked.connect(self.render_next)
        self.previousPageButton.clicked.connect(self.render_previous)
        self.onlyOnlineButton.stateChanged.connect(self.render_only_online)

    def show(self):
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self.reload)
        self._timer.start(1000)
        self.parent.show()

    def init_table(self):
        self.itemTableWidget.setColumnCount(len(self.__class__.colums))
        labels = [col['label'] for col in self.__class__.colums]
        self.itemTableWidget.setHorizontalHeaderLabels(labels)
        self.itemTableWidget.setRowCount(self.page_size)
        for column, column_meta in enumerate(self.__class__.colums):
            self.itemTableWidget.setColumnWidth(column, column_meta['width'])

    def get_queryset(self) -> list[object]:
        pass

    def load(self):
        users = self.get_queryset()
        self.paginator = Paginator(items=users, page_size=self.page_size)
        self.render_curent_page()

    def reload(self):
        queryset = self.get_queryset()
        self.paginator.reload_items(queryset)
        self.render_curent_page()

    def button_checker(self):
        if self.paginator.is_it_first_page():
            self.previousPageButton.setEnabled(False)
        else:
            self.previousPageButton.setEnabled(True)

        if self.paginator.is_it_last_page():
            self.nextPageButton.setEnabled(False)
        else:
            self.nextPageButton.setEnabled(True)

    def add_row(self, item: dict[str, str], row_num: int):
        for col_num, column_meta in enumerate(self.__class__.colums):
            new_item = QtWidgets.QTableWidgetItem(
                str(item.get(column_meta['field_name']))
            )
            self.itemTableWidget.setItem(
                row_num,
                col_num,
                new_item
            )

    def render_rows(self, items: list[object]):
        for row_num, item in enumerate(items):
            columns_data: dict[str, str] = self.get_columns_data(item)
            self.add_row(columns_data, row_num)

    def render_page(self, items: list[object]) -> None:
        self.itemTableWidget.clear()
        self.init_table()
        self.render_rows(items)
        self.pageNumLabel.setText(str(self.paginator.current_page_num))
        self.button_checker()

    def render_curent_page(self):
        self.render_page(self.paginator.get_curent_page())

    @ QtCore.Slot()
    def render_only_online(self, arg__1):
        if arg__1 > 0:
            self.paginator.apply_filter(
                lambda items: [i for i in items if i.is_online()]
            )
        else:
            self.paginator.reset_filter()
        self.render_curent_page()

    @ QtCore.Slot()
    def render_next(self):
        self.render_page(self.paginator.get_next())

    @ QtCore.Slot()
    def render_previous(self):
        self.render_page(self.paginator.get_previous())

    @classmethod
    def start_widget(cls):
        path = Path(__file__).resolve().parent / cls.ui_path
        ui_file = QtCore.QFile(str(path))
        if not ui_file.open(QtCore.QIODevice.ReadOnly):
            reason = ui_file.errorString()
            print(f"Cannot open {path}: {reason}")
            sys.exit(-1)
        loader = QtUiTools.QUiLoader()
        widget = loader.load(ui_file, None)

        user_list_stat = cls(
            parent=widget,
            page_size=10,
            title=cls.title
        )
        user_list_stat.load()
        return user_list_stat
