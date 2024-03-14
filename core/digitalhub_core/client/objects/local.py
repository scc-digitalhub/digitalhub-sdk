"""
Local Client module.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone

from digitalhub_core.client.objects.base import Client
from digitalhub_core.utils.exceptions import BackendError


class ClientLocal(Client):
    """
    Local client.

    The Local client can be used when a remote Digitalhub backend is not available.
    It handles the creation, reading, updating and deleting of objects in memory,
    storing them in a local dictionary.
    The functionality of the Local client is almost the same as the DHCore client.
    Main differences are:
        - Local client does delete objects on cascade.
        - The run execution are forced to be local.
    """

    def __init__(self) -> None:
        """
        Constructor.
        """
        super().__init__()
        self._db: dict[str, dict[str, dict]] = {}

    ########################
    # CRUD
    ########################

    def create_object(self, api: str, obj: dict, **kwargs) -> dict:
        """
        Create an object.

        Parameters
        ----------
        api : str
            The api to create the object with.
        obj : dict
            The object to create.

        Returns
        -------
        dict
            The created object.
        """
        entity_type, _, context_api = self._parse_api(api)
        try:
            # Check if entity_type is valid
            if entity_type is None:
                raise TypeError

            # Check if entity_type exists, if not, create a mapping
            self._db.setdefault(entity_type, {})

            # Base API
            #
            # POST /api/v1/projects
            #
            # Project are not versioned, everything is stored on "entity_id" key
            if not context_api:
                if entity_type == "projects":
                    entity_id = obj["name"]
                    if entity_id in self._db[entity_type]:
                        raise ValueError
                    self._db[entity_type][entity_id] = obj

            # Context API
            #
            # POST /api/v1/-/<project-name>/artifacts
            # POST /api/v1/-/<project-name>/functions
            # POST /api/v1/-/<project-name>/runs
            #
            # Runs and tasks are not versioned, so we keep name as entity_id.
            # We have both "name" and "id" attributes for versioned objects so we use them as storage keys.
            # The "latest" key is used to store the latest version of the object.
            else:
                entity_id = obj["id"]
                name = obj.get("name", entity_id)
                self._db[entity_type].setdefault(name, {})
                if entity_id in self._db[entity_type][name]:
                    raise ValueError
                self._db[entity_type][name][entity_id] = obj
                self._db[entity_type][name]["latest"] = obj

            # Return the created object
            return obj

        # Key error are possibly raised by accessing invalid objects
        except (KeyError, TypeError):
            msg = self._format_msg(1, entity_type=entity_type)
            raise BackendError(msg)

        # If try to create already existing object
        except ValueError:
            msg = self._format_msg(2, entity_type=entity_type, entity_id=entity_id)
            raise BackendError(msg)

    def read_object(self, api: str, **kwargs) -> dict:
        """
        Get an object.

        Parameters
        ----------
        api : str
            The api to get the object with.

        Returns
        -------
        dict or None
            The object, or None if it doesn't exist.
        """
        entity_type, entity_id, context_api = self._parse_api(api)
        if entity_id is None:
            msg = self._format_msg(4)
            raise BackendError(msg)
        try:
            # Base API
            #
            # GET /api/v1/projects/<entity_id>
            #
            # self._parse_api() should return only entity_type

            if not context_api:
                obj = self._db[entity_type][entity_id]

                # If the object is a project, we need to add the project spec,
                # for example artifacts, functions, workflows, etc.
                # Technically we have only projects that access base apis,
                # we check entity_type just in case we add something else.
                if entity_type == "projects":
                    obj = self._get_project_spec(obj, entity_id)

            # Context API
            #
            # GET /api/v1/-/<project-name>/runs/<entity_id>
            # GET /api/v1/-/<project-name>/artifacts/<entity_id>
            # GET /api/v1/-/<project-name>/functions/<entity_id>
            #
            # self._parse_api() should return entity_type and entity_id/version

            else:
                for _, v in self._db[entity_type].items():
                    obj = v[entity_id]
                    break

            return obj

        except KeyError:
            msg = self._format_msg(3, entity_type=entity_type, entity_id=entity_id)
            raise BackendError(msg)

    def update_object(self, api: str, obj: dict, **kwargs) -> dict:
        """
        Update an object.

        Parameters
        ----------
        obj : dict
            The object to update.
        api : str
            The api to update the object with.

        Returns
        -------
        dict
            The updated object.
        """
        entity_type, entity_id, context_api = self._parse_api(api)
        try:
            # API example
            #
            # PUT /api/v1/projects/<entity_id>

            if not context_api:
                self._db[entity_type][entity_id] = obj

            # Context API
            #
            # PUT /api/v1/-/<project-name>/runs/<entity_id>
            # PUT /api/v1/-/<project-name>/artifacts/<entity_id>

            else:
                name = obj.get("name", entity_id)
                self._db[entity_type][name][entity_id] = obj

        except KeyError:
            msg = self._format_msg(3, entity_type=entity_type, entity_id=entity_id)
            raise BackendError(msg)

        return obj

    def delete_object(self, api: str, **kwargs) -> dict:
        """
        Delete an object.

        Parameters
        ----------
        api : str
            The api to delete the object with.

        Returns
        -------
        dict
            A generic dictionary.
        """
        entity_type, entity_id, context_api = self._parse_api(api)
        try:
            # Base API
            #
            # DELETE /api/v1/projects/<entity_id>

            if not context_api:
                obj = self._db[entity_type].pop(entity_id)

            # Context API
            #
            # DELETE /api/v1/-/<project-name>/artifacts/<entity_id>
            #
            # We do not handle cascade in local client and
            # in the sdk we selectively delete objects by id,
            # not by name nor entity_type.

            else:
                reset_latest = False
                name = None
                for _, v in self._db[entity_type].items():
                    obj = v.pop(entity_id)
                    # Handle latest
                    if v["latest"]["id"] == entity_id:
                        name = v["latest"].get("name", entity_id)
                        v.pop("latest")
                        reset_latest = True
                    break

                if name is not None:
                    # Pop name if empty
                    if not self._db[entity_type][name]:
                        self._db[entity_type].pop(name)

                    # Handle latest
                    elif reset_latest:
                        latest_uuid = None
                        latest_date = None
                        for k, v in self._db[entity_type][name].items():
                            # Accept only ISO format
                            fallback = datetime.fromtimestamp(0, timezone.utc)
                            try:
                                current_created = datetime.fromisoformat(v.get("metadata", {}).get("created"))
                                if current_created.tzinfo is None:
                                    current_created = current_created.replace(tzinfo=timezone.utc)
                            except ValueError:
                                current_created = fallback

                            if latest_date is None or current_created > latest_date:
                                latest_uuid = k
                                latest_date = current_created

                        if latest_uuid is not None:
                            self._db[entity_type][name]["latest"] = self._db[entity_type][name][latest_uuid]

        except KeyError:
            msg = self._format_msg(3, entity_type=entity_type, entity_id=entity_id)
            raise BackendError(msg)
        return {"deleted": obj}

    def list_objects(self, api: str, **kwargs) -> list:
        """
        List objects.

        Parameters
        ----------
        api : str
            The api to list the objects with.

        Returns
        -------
        list | None
            The list of objects.
        """
        entity_type, _, _ = self._parse_api(api)
        name = kwargs.get("params", {}).get("name")
        if name is not None:
            return [self._db[entity_type][name]["latest"]]
        return [v["latest"] for _, v in self._db[entity_type].items()]

    ########################
    # Helpers
    ########################

    def _parse_api(self, api: str) -> list[str]:
        """
        Parse the given API.

        Parameters
        ----------
        api : str
            The API to parse.

        Returns
        -------
        list[str]
            The parsed API elements.
        """
        # Remove prefix from API
        api = api.removeprefix("/api/v1/")

        # Set context flag by default to False
        context_api = False

        # Remove context prefix from API and set context flag to True
        if api.startswith("-/"):
            context_api = True
            api = api[2:]

        # Return parsed elements
        return self._parse_api_elements(api, context_api)

    @staticmethod
    def _parse_api_elements(api: str, context_api: bool) -> tuple:
        """
        Parse the elements from the given API.
        Elements returned are: entity_type, entity_id, context_api.

        Parameters
        ----------
        api : str
            The parsed API.
        context_api : bool
            True if the API is a context API.

        Returns
        -------
        tuple
            The parsed elements from the API.
        """
        # Split API path
        parsed = api.split("/")

        # Base API for versioned objects

        # POST /api/v1/<entity_type>
        # Returns entity_type, None, False
        if len(parsed) == 1 and not context_api:
            return parsed[0], None, context_api

        # GET/DELETE/UPDATE /api/v1/<entity_type>/<entity_id>
        # Return entity_type, entity_id, False
        if len(parsed) == 2 and not context_api:
            return parsed[0], parsed[1], context_api

        # Context API for versioned objects

        # POST /api/v1/-/<project>/<entity_type>
        # Returns entity_type, None, True
        if len(parsed) == 2 and context_api:
            return parsed[1], None, context_api

        # GET/DELETE/UPDATE /api/v1/-/<project>/<entity_type>/<entity_id>
        # Return entity_type, entity_id, True
        if len(parsed) == 3 and context_api:
            return parsed[1], parsed[2], context_api

    def _get_project_spec(self, obj: dict, name: str) -> dict:
        """
        Read the project spec.

        Parameters
        ----------
        obj : dict
            The project object.
        name : str
            The project name.

        Returns
        -------
        dict
            The project object with the spec.
        """
        # Deepcopy to avoid modifying the original object
        project = deepcopy(obj)
        spec = project.get("spec", {})

        # Get all entities associated with the project specs
        projects_entities = [k for k, _ in self._db.items() if k not in ["projects", "runs", "tasks"]]

        for entity_type in projects_entities:
            # Get all objects of the entity type for the project
            objs = self._db[entity_type]

            # Set empty list
            spec[entity_type] = []

            # Cycle through named objects
            for _, named_entities in objs.items():
                # Get latest version
                for version, entity in named_entities.items():
                    if version != "latest":
                        continue

                    # Deepcopy to avoid modifying the original object
                    copied = deepcopy(entity)

                    # Remove spec if not embedded
                    if not copied.get("metadata", {}).get("embedded", True):
                        copied.pop("spec", None)

                    # Add to project spec
                    if copied["project"] == name:
                        spec[entity_type].append(copied)

        return project

    ########################
    # Utils
    ########################

    @staticmethod
    def _format_msg(
        error_code: int,
        entity_type: str = None,
        entity_id: str = None,
    ) -> str:
        """
        Format a message.

        Parameters
        ----------
        error_code : int
            Error code.
        project : str
            Project name.
        entity_type : str
            Entity type.
        entity_id : str
            Entity ID.

        Returns
        -------
        str
            The formatted message.
        """
        msg = {
            1: f"Object '{entity_type}' to create is not valid",
            2: f"Object '{entity_type}' with id '{entity_id}' already exists",
            3: f"Object '{entity_type}' with id '{entity_id}' not found",
            4: "Must provide entity_id to read an object",
        }
        return msg[error_code]

    ########################
    # Interface methods
    ########################

    @staticmethod
    def is_local() -> bool:
        """
        Declare if Client is local.

        Returns
        -------
        bool
            True
        """
        return True
