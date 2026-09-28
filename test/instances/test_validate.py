# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0
from pathlib import Path

from .._digitalhub_test_helpers.validate_entities import create_test_validate

TestValidate = create_test_validate(Path(__file__).parent)
