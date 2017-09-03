from PyQt5.QtCore import QFile, QStringListModel, Qt
from PyQt5.QtGui import QCursor, QKeySequence, QTextCursor
from PyQt5.QtWidgets import (QAction, QApplication, QCompleter, QMainWindow,
        QMessageBox, QTextEdit)

import customcompleter_rc


class TextEdit(QTextEdit):
    def __init__(self, parent=None):
        super(TextEdit, self).__init__(parent)

        self._completer = None
        '''
        self.setPlainText(
                "This TextEdit provides autocompletions for words that have "
                "more than 3 characters. You can trigger autocompletion "
                "using %s" % QKeySequence("Ctrl+E").toString(
                        QKeySequence.NativeText))
        '''
        self.setPlainText('')
    def setCompleter(self, c):
        if self._completer is not None:
            self._completer.activated.disconnect()

        self._completer = c

        c.setWidget(self)
        c.setCompletionMode(QCompleter.PopupCompletion)
        c.setCaseSensitivity(Qt.CaseInsensitive)
        c.activated.connect(self.insertCompletion)

    def completer(self):
        return self._completer

    def insertCompletion(self, completion):
        if self._completer.widget() is not self:
            return

        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        if extra is not 0:
            tc.insertText(completion[-extra:])
            self.setTextCursor(tc)

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)

        return tc.selectedText()

    def focusInEvent(self, e):
        if self._completer is not None:
            self._completer.setWidget(self)

        super(TextEdit, self).focusInEvent(e)

    def keyPressEvent(self, e):
        if self._completer is not None and self._completer.popup().isVisible():
            # The following keys are forwarded by the completer to the widget.
            if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                e.ignore()
                # Let the completer do default behavior.
                return

        isShortcut = ((e.modifiers() & Qt.ControlModifier) != 0 and e.key() == Qt.Key_0)
        if self._completer is None or not isShortcut:
            # Do not process the shortcut when we have a completer.
            super(TextEdit, self).keyPressEvent(e)

        ctrlOrShift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if self._completer is None or (ctrlOrShift and len(e.text()) == 0):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        hasModifier = (e.modifiers() != Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()

        if not isShortcut and (hasModifier or len(e.text()) == 0 or len(completionPrefix) < 2 or e.text()[-1] in eow):
            self._completer.popup().hide()
            return

        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(
                    self._completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self._completer.popup().sizeHintForColumn(0) + self._completer.popup().verticalScrollBar().sizeHint().width())
        self._completer.complete(cr)


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)

        self.createMenu()

        self.completingTextEdit = TextEdit()
        self.completer = QCompleter(self)
        self.completer.setModel(self.modelFromFile(':/resources/wordlist.txt'))
        self.completer.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
        self.completer.setCaseSensitivity(Qt.CaseInsensitive)
        self.completer.setWrapAround(False)
        self.completingTextEdit.setCompleter(self.completer)

        self.setCentralWidget(self.completingTextEdit)
        self.resize(500, 300)
        self.setWindowTitle("Completer")

    def createMenu(self):
        exitAction = QAction("Exit", self)
        aboutAct = QAction("About", self)
        aboutQtAct = QAction("About Qt", self)

        exitAction.triggered.connect(QApplication.instance().quit)
        aboutAct.triggered.connect(self.about)
        aboutQtAct.triggered.connect(QApplication.instance().aboutQt)

        fileMenu = self.menuBar().addMenu("File")
        fileMenu.addAction(exitAction)

        helpMenu = self.menuBar().addMenu("About")
        helpMenu.addAction(aboutAct)
        helpMenu.addAction(aboutQtAct)

    def modelFromFile(self, fileName):
        f = QFile(fileName)
        if not f.open(QFile.ReadOnly):
            return QStringListModel(self.completer)

        QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

        words = []
        while not f.atEnd():
            line = f.readLine().trimmed()
            if line.length() != 0:
                try:
                    line = str(line, encoding='ascii')
                except TypeError:
                    line = str(line)

                words.append(line)

        QApplication.restoreOverrideCursor()

        return QStringListModel(words, self.completer)

    def about(self):
        QMessageBox.about(self, "About",
                "This example demonstrates the different features of the "
                "QCompleter class.")


if __name__ == '__main__':

    import sys

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
