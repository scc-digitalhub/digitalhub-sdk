# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities._processors.base.crud import BaseEntityCRUDProcessor
from digitalhub.entities._processors.base.special_ops import BaseEntitySpecialOpsProcessor
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
from digitalhub.entities._processors.context.key import ContextEntityKeyProcessor
from digitalhub.entities._processors.context.material import ContextEntityMaterialProcessor
from digitalhub.entities._processors.context.metrics import ContextEntityMetricsProcessor
from digitalhub.entities._processors.context.run import ContextEntityRunProcessor
from digitalhub.entities._processors.context.search import ContextEntitySearchProcessor
from digitalhub.entities._processors.context.secret import ContextEntitySecretProcessor

# Base processor singletons
base_crud_processor = BaseEntityCRUDProcessor()
base_special_ops_processor = BaseEntitySpecialOpsProcessor()

# Context processor singletons
crud_processor = ContextEntityCRUDProcessor()
material_processor = ContextEntityMaterialProcessor(crud_processor)
executable_processor = ContextEntityExecutableProcessor(crud_processor)
key_processor = ContextEntityKeyProcessor()
secret_processor = ContextEntitySecretProcessor()
run_processor = ContextEntityRunProcessor()
metrics_processor = ContextEntityMetricsProcessor()
search_processor = ContextEntitySearchProcessor()
