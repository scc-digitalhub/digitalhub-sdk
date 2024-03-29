from __future__ import annotations

import importlib.util as imputil
import inspect
import sys
import typing
from importlib import import_module
from os import path
from pathlib import Path
from types import ModuleType

from digitalhub_core.entities.functions.crud import get_function
from digitalhub_core.utils.generic_utils import decode_string
from digitalhub_core.utils.logger import LOGGER

if typing.TYPE_CHECKING:
    from digitalhub_core.entities.functions.entity import Function
    from digitalhub_core_kfp.entities.functions.spec import FunctionSpecKFP


def get_dhcore_function(function_string: str) -> Function:
    """
    Get DHCore function.

    Parameters
    ----------
    function_string : str
        Function string.

    Returns
    -------
    Function
        DHCore function.
    """
    splitted = function_string.split("://")[1].split("/")
    function_name, function_version = splitted[1].split(":")
    LOGGER.info(f"Getting function {function_name}:{function_version}.")
    try:
        return get_function(splitted[0], function_name, function_version)
    except Exception:
        msg = f"Error getting function {function_name}:{function_version}."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def save_function_source(path: str, spec: FunctionSpecKFP) -> str:
    """
    Save function source.

    Parameters
    ----------
    path : str
        Path to the function source.
    function : FunctionSpecMlrun
        DHCore function spec.

    Returns
    -------
    path
        Path to the function source.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        path = path / spec.source.source
        path.parent.mkdir(parents=True, exist_ok=True)
        if "code" in spec.source.code:
            code = spec.source.code
        else:
            code = decode_string(spec.source.base64)
        path.write_text(code)
        return str(path)
    except Exception as err:
        msg = "Error saving function source: " + str(err)
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def parse_function_specs(spec: FunctionSpecKFP) -> dict:
    """
    Parse function specs.

    Parameters
    ----------
    function : FunctionSpecMlrun
        DHCore function spec.

    Returns
    -------
    dict
        Function specs.
    """
    try:
        return {
            "image": spec.image,
            "tag": spec.tag,
            "handler": spec.handler,
            "requirements": spec.requirements,
        }
    except AttributeError:
        msg = "Error parsing function specs."
        LOGGER.error(msg)
        raise RuntimeError(msg)


def get_kfp_pipeline(name: str, function_source: str, function_specs: dict) -> dict:
    """
    Get KFP pipeline.

    Parameters
    ----------
    name : str
        Name of the KFP pipeline.
    function_source : str
        Source of the function.
    function_specs : dict
        Specifications of the function.

    Returns
    -------
    dict
        KFP pipeline.
    """
    try:
        if not path.isfile(function_source):
            raise OSError(f"source file {function_source} not found")
        abspath = path.abspath(function_source)
        if abspath not in sys.path:
            sys.path.append(abspath)
        handler = _load_module(function_source, function_specs.get("handler"))

        return handler
    except Exception:
        msg = "Error getting KFP pipeline."
        LOGGER.exception(msg)
        raise RuntimeError(msg)


def _load_module(file_name, handler):
    """Load module from file name"""
    module = None
    if file_name:
        path = Path(file_name)
        mod_name = path.name
        if path.suffix:
            mod_name = mod_name[: -len(path.suffix)]
        spec = imputil.spec_from_file_location(mod_name, file_name)
        if spec is None:
            msg = "Error loading KFP pipeline source."
            LOGGER.exception(msg)
            raise RuntimeError(msg)

        module = imputil.module_from_spec(spec)
        spec.loader.exec_module(module)

    class_args = {}

    return _get_handler_extended(handler, class_args, namespaces=module)


def _get_handler_extended(handler_path: str, class_args: dict = {}, namespaces=None):
    """get function handler from [class_name::]handler string

    :param handler_path:  path to the function ([class_name::]handler)
    :param class_args:    optional dict of class init kwargs
    :param namespaces:    one or list of namespaces/modules to search the handler in
    :return: function handler (callable)
    """
    if "::" not in handler_path:
        return _get_function_to_exec(handler_path, namespaces)

    splitted = handler_path.split("::")
    class_path = splitted[0].strip()
    handler_path = splitted[1].strip()

    class_object = _get_class(class_path, namespaces)
    try:
        instance = class_object(**class_args)
    except TypeError as exc:
        raise TypeError(f"failed to init class {class_path}\n args={class_args}") from exc

    if not hasattr(instance, handler_path):
        raise ValueError(f"handler ({handler_path}) specified but doesnt exist in class {class_path}")
    return getattr(instance, handler_path)


def _module_to_namespace(namespace):
    if isinstance(namespace, ModuleType):
        members = inspect.getmembers(namespace, lambda o: inspect.isfunction(o) or isinstance(o, type))
        return {key: mod for key, mod in members}
    return namespace


def _search_in_namespaces(name, namespaces):
    """search the class/function in a list of modules"""
    if not namespaces:
        return None
    if not isinstance(namespaces, list):
        namespaces = [namespaces]
    for namespace in namespaces:
        namespace = _module_to_namespace(namespace)
        if name in namespace:
            return namespace[name]
    return None


def _get_class(class_name, namespace=None):
    """return class object from class name string"""
    if isinstance(class_name, type):
        return class_name
    class_object = _search_in_namespaces(class_name, namespace)
    if class_object is not None:
        return class_object

    try:
        class_object = _create_class(class_name)
    except (ImportError, ValueError) as exc:
        raise ImportError(f"Failed to import {class_name}") from exc
    return class_object


def _create_class(pkg_class: str):
    """Create a class from a package.module.class string

    :param pkg_class:  full class location,
                       e.g. "sklearn.model_selection.GroupKFold"
    """
    splits = pkg_class.split(".")
    clfclass = splits[-1]
    pkg_module = splits[:-1]
    class_ = getattr(import_module(".".join(pkg_module)), clfclass)
    return class_


def _get_function_to_exec(function, namespace):
    """return function callable object from function name string"""
    if callable(function):
        return function

    function = function.strip()
    if function.startswith("("):
        if not function.endswith(")"):
            raise ValueError('function expression must start with "(" and end with ")"')
        return eval("lambda event: " + function[1:-1], {}, {})
    function_object = _search_in_namespaces(function, namespace)
    if function_object is not None:
        return function_object

    try:
        function_object = _create_function(function)
    except (ImportError, ValueError) as exc:
        raise ImportError(f"state/function init failed, handler '{function}' not found") from exc
    return function_object


def _create_function(pkg_func: str):
    """Create a function from a package.module.function string

    :param pkg_func:  full function location"
    """
    splits = pkg_func.split(".")
    pkg_module = ".".join(splits[:-1])
    cb_fname = splits[-1]
    pkg_module = __import__(pkg_module, fromlist=[cb_fname])
    function_ = getattr(pkg_module, cb_fname)
    return function_
