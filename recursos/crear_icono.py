"""Genera el icono de la aplicación (recursos/icono.ico).

Requiere Pillow:  pip install pillow
    python recursos/crear_icono.py
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

TAM = 256
AZUL = (37, 99, 235)
AZUL_OSC = (29, 78, 216)
VERDE = (22, 163, 74)
PAPEL = (255, 255, 255)
LINEA = (203, 213, 225)


def _rect_redondeado(draw, caja, radio, relleno):
    draw.rounded_rectangle(caja, radius=radio, fill=relleno)


def crear() -> Image.Image:
    img = Image.new("RGBA", (TAM, TAM), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Fondo redondeado con un borde inferior más oscuro
    _rect_redondeado(d, (8, 8, TAM - 8, TAM - 8), 48, AZUL_OSC)
    _rect_redondeado(d, (8, 8, TAM - 8, TAM - 16), 48, AZUL)

    # Hoja de papel con esquina doblada
    px0, py0, px1, py1 = 72, 52, 184, 204
    pliegue = 34
    d.polygon(
        [(px0, py0), (px1 - pliegue, py0), (px1, py0 + pliegue), (px1, py1), (px0, py1)],
        fill=PAPEL,
    )
    d.polygon(
        [(px1 - pliegue, py0), (px1 - pliegue, py0 + pliegue), (px1, py0 + pliegue)],
        fill=LINEA,
    )

    # Líneas de texto
    for i in range(4):
        y = py0 + 34 + i * 24
        d.rounded_rectangle((px0 + 16, y, px1 - 16 - (18 if i == 3 else 0), y + 8),
                            radius=4, fill=LINEA)

    # Insignia verde con flecha hacia abajo (transformar / adaptar)
    cx, cy, r = 186, 190, 40
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=VERDE, outline=PAPEL, width=6)
    d.line((cx, cy - 16, cx, cy + 14), fill=PAPEL, width=10)
    d.polygon([(cx - 16, cy + 4), (cx + 16, cy + 4), (cx, cy + 24)], fill=PAPEL)

    return img


def main() -> None:
    carpeta = os.path.dirname(os.path.abspath(__file__))
    img = crear()
    ruta_ico = os.path.join(carpeta, "icono.ico")
    img.save(ruta_ico, sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    img.save(os.path.join(carpeta, "icono.png"))
    print("Creado", ruta_ico)


if __name__ == "__main__":
    main()
