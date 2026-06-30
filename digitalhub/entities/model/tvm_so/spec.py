# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from digitalhub.entities.model._tvm.spec import ModelSpecTvm, ModelValidatorTvm


class ModelSpecTvmSo(ModelSpecTvm):
    """
    ModelSpecTvmSo specifications. Compiled model.so produced by tvm+compile.
    """

    def __init__(
        self,
        path: str,
        framework: str | None = None,
        algorithm: str | None = None,
        parameters: dict | None = None,
        entry: str | None = None,
        inputs: list[dict] | None = None,
        outputs: list[dict] | None = None,
        target: str | None = None,
        opt_level: int | None = None,
        manifest: dict | None = None,
    ) -> None:
        super().__init__(path, framework, algorithm, parameters, entry, inputs, outputs)
        self.target = target
        self.opt_level = opt_level
        self.manifest = manifest


class ModelValidatorTvmSo(ModelValidatorTvm):
    """
    ModelValidatorTvmSo validator.
    """

    target: str | None = None
    """TVM hardware target the .so was compiled for (e.g. 'llvm -mcpu=x86-64-v2')."""

    opt_level: int | None = None
    """TVM optimization level used at compile (0-3)."""

    manifest: dict | None = None
    """Parsed manifest.json produced by the compile job."""
