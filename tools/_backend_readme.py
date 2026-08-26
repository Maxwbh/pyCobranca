"""Backend PEP 517: empacota com o README em URLs absolutas.

Cola fina sobre ``setuptools.build_meta``. Toda a regra de conversão — e o
porquê dela — está em :mod:`_readme_urls`, que é texto puro e não importa
``setuptools``, para a suíte de testes cobri-la sem depender do ambiente de
build.

Ligado em ``pyproject.toml``::

    [build-system]
    build-backend = "_backend_readme"
    backend-path = ["tools"]

Os dois módulos precisam entrar no sdist (ver ``MANIFEST.in``), senão construir
um wheel a partir do sdist falha por backend ausente.
"""

from __future__ import annotations

from _readme_urls import readme_publicavel
from setuptools import build_meta as _origem

# Sem README convertido: nada aqui lê o long_description.
get_requires_for_build_wheel = _origem.get_requires_for_build_wheel
get_requires_for_build_sdist = _origem.get_requires_for_build_sdist
get_requires_for_build_editable = _origem.get_requires_for_build_editable


def prepare_metadata_for_build_wheel(metadata_directory, config_settings=None):
    with readme_publicavel():
        return _origem.prepare_metadata_for_build_wheel(metadata_directory, config_settings)


def prepare_metadata_for_build_editable(metadata_directory, config_settings=None):
    with readme_publicavel():
        return _origem.prepare_metadata_for_build_editable(metadata_directory, config_settings)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):
    with readme_publicavel():
        return _origem.build_wheel(wheel_directory, config_settings, metadata_directory)


def build_sdist(sdist_directory, config_settings=None):
    with readme_publicavel():
        return _origem.build_sdist(sdist_directory, config_settings)


def build_editable(wheel_directory, config_settings=None, metadata_directory=None):
    with readme_publicavel():
        return _origem.build_editable(wheel_directory, config_settings, metadata_directory)
