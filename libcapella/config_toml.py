##
##

import logging
import sys
from libcapella.config_data import CapellaConfigData
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib

logger = logging.getLogger('libcapella.config_toml')
logger.addHandler(logging.NullHandler())


class CapellaTomlConfig(CapellaConfigData):

    def __init__(self, filename: str):
        super().__init__()
        self.filename = filename
        self.toml_dict = {}

        self.read_config_file()
        self.read_config()

    def read_config_file(self):
        try:
            with open(self.filename, "rb") as toml_file:
                self.toml_dict = tomllib.load(toml_file)
        except tomllib.TOMLDecodeError as err:
            RuntimeError(f"can not read config file {self.filename}: invalid TOML: {err}")

    def read_config(self):
        if self.toml_dict.get("capella", {}).get("api", {}).get("host"):
            self._api_host = self.toml_dict.get("capella").get("api").get("host")
        if self.toml_dict.get("capella", {}).get("token"):
            self._token = self.toml_dict.get("capella").get("token")
        if self.toml_dict.get("capella", {}).get("organization", {}).get("name"):
            self._organization_name = self.toml_dict.get("capella").get("organization").get("name")
        if self.toml_dict.get("capella", {}).get("organization", {}).get("id"):
            self._organization_id = self.toml_dict.get("capella").get("organization").get("id")
        if self.toml_dict.get("capella", {}).get("project", {}).get("name"):
            self._project_name = self.toml_dict.get("capella").get("project").get("name")
        if self.toml_dict.get("capella", {}).get("project", {}).get("id"):
            self._project_id = self.toml_dict.get("capella").get("project").get("id")
        if self.toml_dict.get("capella", {}).get("user", {}).get("email"):
            self._account_email = self.toml_dict.get("capella").get("user").get("email")
        if self.toml_dict.get("capella", {}).get("user", {}).get("id"):
            self._account_id = self.toml_dict.get("capella").get("user").get("id")
        if self.toml_dict.get("capella", {}).get("database", {}).get("name"):
            self._database_name = self.toml_dict.get("capella").get("database").get("name")
        if self.toml_dict.get("capella", {}).get("columnar", {}).get("name"):
            self._columnar_name = self.toml_dict.get("capella").get("columnar").get("name")
