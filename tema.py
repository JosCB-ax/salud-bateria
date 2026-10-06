"""Tema claro u oscuro de la ventana, siguiendo al sistema si se elige "automático"."""

from __future__ import annotations

import platform

from lectores import ejecutar

PALETAS = {
    "claro": {"bg": "#f3f4f6", "panel": "#ffffff", "fg": "#1d2330", "mut": "#666b75",
              "linea": "#e4e6ea", "rejilla": "#eef0f3", "acc": "#2f6fed", "sel": "#dbe6fd"},
    "oscuro": {"bg": "#1b1d22", "panel": "#24272e", "fg": "#e8eaf0", "mut": "#9aa0ab",
               "linea": "#363a44", "rejilla": "#2e323a", "acc": "#6d9bff", "sel": "#2f3f66"},
}


def sistema_oscuro() -> bool:
    so = platform.system()
    if so == "Windows":
        try:
            import winreg
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
                return winreg.QueryValueEx(k, "AppsUseLightTheme")[0] == 0
        except OSError:
            return False
    if so == "Darwin":
        return "Dark" in ejecutar(["defaults", "read", "-g", "AppleInterfaceStyle"])
    return "dark" in ejecutar(["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"]).lower()


def elegir(preferencia: str) -> str:
    """'automatico', 'claro' u 'oscuro' -> nombre de la paleta a usar."""
    if preferencia in PALETAS:
        return preferencia
    return "oscuro" if sistema_oscuro() else "claro"


def aplicar(root, nombre: str) -> dict:
    from tkinter import ttk
    p = PALETAS[nombre]
    estilo = ttk.Style(root)
    if nombre == "claro" and "vista" in estilo.theme_names():
        estilo.theme_use("vista")
    else:
        estilo.theme_use("clam")
        estilo.configure(".", background=p["bg"], foreground=p["fg"], fieldbackground=p["panel"],
                         bordercolor=p["linea"], lightcolor=p["bg"], darkcolor=p["bg"],
                         troughcolor=p["linea"], insertcolor=p["fg"])
        estilo.configure("TButton", background=p["panel"], padding=(8, 3))
        estilo.map("TCombobox", fieldbackground=[("readonly", p["panel"])], foreground=[("readonly", p["fg"])],
                   selectbackground=[("readonly", p["panel"])], selectforeground=[("readonly", p["fg"])])
        estilo.map("TButton", background=[("active", p["sel"]), ("disabled", p["bg"])],
                   foreground=[("disabled", p["mut"])])
        estilo.configure("TNotebook", background=p["bg"], tabmargins=0)
        estilo.configure("TNotebook.Tab", background=p["bg"], padding=(10, 4))
        estilo.map("TNotebook.Tab", background=[("selected", p["panel"])])
        estilo.configure("Treeview", background=p["panel"], fieldbackground=p["panel"], foreground=p["fg"])
        estilo.configure("Treeview.Heading", background=p["bg"], foreground=p["fg"])
        estilo.map("Treeview", background=[("selected", p["sel"])], foreground=[("selected", p["fg"])])
        estilo.configure("TCheckbutton", background=p["bg"], foreground=p["fg"])
        estilo.map("TCheckbutton", background=[("active", p["bg"])])
        estilo.configure("Horizontal.TProgressbar", background=p["acc"])
    estilo.configure("Treeview", rowheight=26)
    root.configure(bg=p["bg"])
    root.option_add("*Toplevel.background", p["bg"])
    root.option_add("*TCombobox*Listbox.background", p["panel"])
    root.option_add("*TCombobox*Listbox.foreground", p["fg"])
    if platform.system() == "Windows":
        _barra_titulo_oscura(root, nombre == "oscuro")
    return p


def _barra_titulo_oscura(ventana, oscura: bool) -> None:
    """Pone la barra de título de Windows 10/11 a juego con el tema."""
    try:
        import ctypes
        ventana.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(ventana.winfo_id())
        valor = ctypes.c_int(1 if oscura else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(valor), ctypes.sizeof(valor))
    except Exception:  # noqa: BLE001 - versiones antiguas de Windows no lo soportan
        pass
