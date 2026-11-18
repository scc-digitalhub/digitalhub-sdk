# SPDX-FileCopyrightText: © 2025 DSLab - Fondazione Bruno Kessler
#
# SPDX-License-Identifier: Apache-2.0

from digitalhub.entities._processors.base.crud import BaseEntityCRUDProcessor
from digitalhub.entities._processors.base.special_ops import BaseEntitySpecialOpsProcessor
from digitalhub.entities._processors.context.control import ContextEntityControlProcessor
from digitalhub.entities._processors.context.crud import ContextEntityCRUDProcessor
from digitalhub.entities._processors.context.executable import ContextEntityExecutableProcessor
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
control_processor = ContextEntityControlProcessor()
material_processor = ContextEntityMaterialProcessor(crud_processor)
secret_processor = ContextEntitySecretProcessor()
run_processor = ContextEntityRunProcessor()
executable_processor = ContextEntityExecutableProcessor(crud_processor)
metrics_processor = ContextEntityMetricsProcessor()
search_processor = ContextEntitySearchProcessor(crud_processor)
