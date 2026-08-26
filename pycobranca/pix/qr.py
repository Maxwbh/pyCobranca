"""QR Code real do PIX — matriz de módulos e SVG.

Usa a biblioteca ``qrcode`` (Python puro, dependência do pacote) para gerar a
matriz de módulos consumida pelo backend ReportLab (``pix.qrcode_matrix``) e um
SVG para pré-visualizações.
"""

from __future__ import annotations

from ..exceptions import DependenciaAusente

__all__ = ["qr_matrix", "qr_svg"]


def _qrcode():
    try:
        import qrcode
    except ModuleNotFoundError as exc:  # pragma: no cover - dependência opcional
        raise DependenciaAusente(
            "A biblioteca 'qrcode' é necessária para gerar a imagem do QR do PIX. "
            "Reinstale o pacote: pip install --force-reinstall pycobranca."
        ) from exc
    return qrcode


def qr_matrix(payload: str) -> list[list[int]]:
    """Matriz de módulos (0/1) do QR para o ``payload`` (BR Code).

    Correção de erro nível M (recomendação do manual do PIX) e ``border=0``: a
    matriz sai só com o símbolo.

    A **zona de silêncio** da norma (4 módulos) não é desenhada — ela vem do
    fundo branco do boleto, já que o QR é posicionado com folga em volta. Quem
    consumir a matriz em outro suporte precisa reservar essa margem: sem ela o
    leitor não isola o símbolo do que estiver ao redor.
    """
    qrcode = _qrcode()
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    qr.add_data(payload)
    qr.make(fit=True)
    return [[1 if celula else 0 for celula in linha] for linha in qr.get_matrix()]


def qr_svg(payload: str, *, escala: float = 4.0, cor: str = "#101418") -> str:
    """SVG do QR (com zona de silêncio de 4 módulos) para pré-visualizações."""
    matriz = qr_matrix(payload)
    n = len(matriz)
    borda = 4
    dim = (n + 2 * borda) * escala
    quadrados = "".join(
        f'<rect x="{(c + borda) * escala:.1f}" y="{(r + borda) * escala:.1f}" '
        f'width="{escala:.1f}" height="{escala:.1f}"/>'
        for r, linha in enumerate(matriz)
        for c, celula in enumerate(linha)
        if celula
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {dim:.1f} {dim:.1f}">'
        f'<rect width="{dim:.1f}" height="{dim:.1f}" fill="#fff"/>'
        f'<g fill="{cor}">{quadrados}</g></svg>'
    )
