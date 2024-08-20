from __future__ import annotations

from typing import Literal

from digitalhub_core.entities.task.spec import TaskParamsK8s, TaskSpecK8s


class TaskSpecServe(TaskSpecK8s):
    """Task Serve specification."""

    def __init__(
        self,
        function: str,
        replicas: int | None = None,
        service_type: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(function, **kwargs)

        self.replicas = replicas
        self.service_type = service_type

class TaskParamsServe(TaskParamsK8s):
    """
    TaskParamsServe model.
    """

    replicas: int = None
    service_type: Literal["ClusterIP", "NodePort", "LoadBalancer"] = "NodePort"

class TaskSpecSklearnserveServe(TaskSpecServe):
    """
    TaskSpecSklearnserveServe model.
    """

class TaskParamsSklearnserveServe(TaskParamsServe):
    """
    TaskParamsSklearnserveServe model.
    """

class TaskSpecMlflowserveServe(TaskSpecServe):
    """
    TaskSpecMlflowserveServe model.
    """

class TaskParamsMlflowserveServe(TaskParamsServe):
    """
    TaskParamsMlflowserveServe model.
    """

class TaskSpecHuggingfaceserveServe(TaskSpecServe):
    """
    TaskSpecHuggingfaceserveServe model.
    """
    def __init__(
        self,
        function: str,
        huggingface_task_name: str | None = None,
        backend: str | None = None,
        tokenizer_revision: str | None = None,
        max_length: int | None = None,
        disable_lower_case: bool | None = None,
        disable_special_tokens: bool | None = None,
        dtype: str | None = None,
        trust_remote_code: bool | None = None,
        tensor_input_names: list[str] | None = None,
        return_token_type_ids: bool | None = None,
        return_probabilities: bool | None = None,
        **kwargs,
    ) -> None:
        super().__init__(function, **kwargs)

        self.huggingface_task_name = huggingface_task_name
        self.backend = backend
        self.tokenizer_revision = tokenizer_revision
        self.max_length = max_length
        self.disable_lower_case = disable_lower_case
        self.disable_special_tokens = disable_special_tokens
        self.dtype = dtype
        self.trust_remote_code = trust_remote_code
        self.tensor_input_names = tensor_input_names
        self.return_token_type_ids = return_token_type_ids
        self.return_probabilities = return_probabilities

class TaskParamsHuggingfaceserveServe(TaskParamsServe):
    """
    TaskParamsHuggingfaceserveServe model.
    """

    huggingface_task_name: Literal["sequence-classification", "token-classification", "fill-mask", "text-generation", "text2text-generation"] = None
    """
    Huggingface task name.
    """

    backend: Literal["auto", "vllm", "huggingface"] = None
    """
    Backend type.
    """
    tokenizer_revision: str = None
    """
    Tokenizer revision. 
    """
    max_length: int = None
    """
    Huggingface max sequence length for the tokenizer.
    """
    disable_lower_case: bool = None
    """
    Do not use lower case for the tokenizer.
    """
    disable_special_tokens: bool = None
    """
    The sequences will not be encoded with the special tokens relative to their model
    """
    dtype: Literal["auto", "float32", "float16", "bfloat16", "float", "half"] = None
    """
    Data type to load the weights in.
    """
    trust_remote_code: bool = None
    """
    Allow loading of models and tokenizers with custom code.
    """
    tensor_input_names: list[str] = None
    """
    The tensor input names passed to the model
    """
    return_token_type_ids: bool = None
    """
    Return token type ids
    """
    return_probabilities: bool = None
    """
    Return all probabilities
    """
    disable_log_requests: bool = None
    """
    Disable log requests
    """
    max_log_len: int = None
    """
    Max number of prompt characters or prompt
    """



