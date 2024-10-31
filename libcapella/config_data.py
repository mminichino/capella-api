##
##

import logging

logger = logging.getLogger('libcapella.config_data')
logger.addHandler(logging.NullHandler())


class CapellaConfigData(object):

    def __init__(self):
        self._api_host = "cloudapi.cloud.couchbase.com"
        self._token = None
        self._organization_name = None
        self._organization_id = None
        self._project_name = None
        self._project_id = None
        self._account_email = None
        self._account_id = None
        self._database_name = None
        self._columnar_name = None

    def from_dict(self, data: dict):
        self._api_host = data.get("api_host", self._api_host)
        self._token = data.get("token", self._token)
        self._organization_name = data.get("organization_name", self._organization_name)
        self._organization_id = data.get("organization_id", self._organization_id)
        self._project_name = data.get("project_name", self._project_name)
        self._project_id = data.get("project_id", self._project_id)
        self._account_email = data.get("account_email", self._account_email)
        self._account_id = data.get("account_id", self._account_id)
        self._database_name = data.get("database_name", self._database_name)
        self._columnar_name = data.get("columnar_name", self._columnar_name)

    def set_api_host(self, api_host: str):
        self._api_host = api_host

    def set_token(self, token: str):
        self._token = token

    def set_organization_name(self, organization_name: str):
        self._organization_name = organization_name

    def set_organization_id(self, organization_id: str):
        self._organization_id = organization_id

    def set_project_name(self, project_name: str):
        self._project_name = project_name

    def set_project_id(self, project_id: str):
        self._project_id = project_id

    def set_account_email(self, account_email: str):
        self._account_email = account_email

    def set_account_id(self, account_id: str):
        self._account_id = account_id

    def set_database_name(self, database_name: str):
        self._database_name = database_name

    def set_columnar_name(self, columnar_name: str):
        self._columnar_name = columnar_name

    @property
    def api_host(self):
        return self._api_host

    @property
    def token(self):
        return self._token

    @property
    def organization_name(self):
        return self._organization_name

    @property
    def organization_id(self):
        return self._organization_id

    @property
    def project_name(self):
        return self._project_name

    @property
    def project_id(self):
        return self._project_id

    @property
    def account_email(self):
        return self._account_email

    @property
    def account_id(self):
        return self._account_id

    @property
    def database_name(self):
        return self._database_name

    @property
    def columnar_name(self):
        return self._columnar_name

    def __str__(self):
        return (f"api_host={self.api_host}\n"
                f"token={self.token}\n"
                f"organization_name={self.organization_name}\n"
                f"organization_id={self.organization_id}\n"
                f"project_name={self.project_name}\n"
                f"project_id={self.project_id}\n"
                f"account_email={self.account_email}\n"
                f"account_id={self.account_id}\n"
                f"database_name={self.database_name}\n"
                f"columnar_name={self.columnar_name}\n")
