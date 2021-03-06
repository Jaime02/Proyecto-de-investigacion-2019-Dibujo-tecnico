# -*- coding: utf-8 -*-
from PyQt5.QtWidgets import QApplication
from clases.ventana_principal import VentanaPrincipal
from sys import argv

if __name__ == "__main__":
    evento_principal = QApplication([])
    # Si se ha introducido decidido abrir un archivo directamente, se pasa su dirección como argumento
    if len(argv) > 1:
        programa = VentanaPrincipal(evento_principal, argv[1])
    else:
        programa = VentanaPrincipal(evento_principal)
    evento_principal.exec()
