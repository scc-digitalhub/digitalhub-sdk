from __future__ import annotations

from digitalhub_core.entities.workflow.spec import WorkflowParams, WorkflowSpec
from digitalhub_runtime_kfp.entities.workflow.models import SourceCodeParamsKfp, SourceCodeStructKfp


class WorkflowSpecKFP(WorkflowSpec):
    """
    Specification for a Workflow pipeline.
    """

    def __init__(
        self,
        source: dict | None = None,
        code_src: str | None = None,
        handler: str | None = None,
        code: str | None = None,
        base64: str | None = None,
        lang: str | None = None,
        image: str | None = None,
        tag: str | None = None,
        workflow: str | None = None,
    ) -> None:
        super().__init__()

        self.image = image
        self.tag = tag
        self.workflow = workflow

        # Give source precedence
        if source is not None:
            source_dict = source
        else:
            source_dict = {
                "source": code_src,
                "handler": handler,
                "code": code,
                "base64": base64,
                "lang": lang,
            }

        source_checked = self.source_check(source_dict)
        self.source = SourceCodeStructKfp(**source_checked)

    @staticmethod
    def source_check(source: dict) -> dict:
        """
        Check source.

        Parameters
        ----------
        source : dict
            Source.

        Returns
        -------
        dict
            Checked source.
        """
        return SourceCodeStructKfp.source_check(source)

    def show_source_code(self) -> str:
        """
        Show source code.

        Returns
        -------
        str
            Source code.
        """
        return self.source.show_source_code()

    def to_dict(self) -> dict:
        """
        Override to_dict to exclude code from source.

        Returns
        -------
        dict
            Dictionary representation of the object.
        """
        dict_ = super().to_dict()
        dict_["source"] = self.source.to_dict()
        return dict_


class WorkflowParamsKFP(WorkflowParams, SourceCodeParamsKfp):
    """
    Workflow kfp parameters model.
    """

    image: str = None
    """Name of the Workflow's container image."""

    tag: str = None
    """Tag of the Workflow's container image."""

    workflow: str = None
    """YAML of the Workflow."""