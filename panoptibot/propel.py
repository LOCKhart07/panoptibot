import logging
import math
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import dotenv
import requests
import urllib3
import yaml
from propel_client.constants import PROPEL_SERVICE_BASE_URL
from propel_client.cred_storage import CredentialStorage
from propel_client.propel import PropelClient

logger = logging.getLogger("propel")
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


dotenv.load_dotenv(override=True)

HTTP_OK = 200


class Agent:
    """Agent"""

    def __init__(self, name: str, client: PropelClient):
        """Constructor"""
        self.name = name
        self.client = client

    def get(self):
        """Get the agent"""
        logger.info(f"Getting agent {self.name}")
        return self.client.agents_get(self.name)

    def restart(self):
        """Restart the agent"""
        logger.info(f"Restarting agent {self.name}")
        return self.client.agents_restart(self.name)

    def stop(self):
        """Stop the agent"""
        logger.info(f"Stopping agent {self.name}")
        return self.client.agents_stop(self.name)

    def get_agent_code(self):
        """Get the agent code"""
        logger.info(f"Getting agent code for {self.name}")
        agent_status = self.get()
        tendermint_p2p_url = agent_status.get("tendermint_p2p_url", None)
        if not tendermint_p2p_url:
            return None

        agent_code = tendermint_p2p_url.split(".")[0].split("-")[-1]
        return agent_code

    def get_agent_state(self):
        """Get the agent state"""
        logger.info(f"Getting status for agent {self.name}")
        data = self.get()
        return data.get("agent_state", None)

    def get_agent_health(self) -> Tuple[bool, Dict]:
        """Get the agent status"""
        logger.info(f"Checking status for agent {self.name}")
        agent_code = self.get_agent_code()
        healthcheck_url = (
            f"https://{agent_code}.agent.propel.autonolas.tech/healthcheck"
        )

        try:
            response = requests.get(healthcheck_url, verify=False)
            if response.status_code != HTTP_OK:
                return False, {}
            response_json = response.json()
            is_healthy = response_json["is_transitioning_fast"]
            return is_healthy, response_json
        except Exception:
            return False, {}

    def healthcheck(self) -> Tuple[bool, Optional[str]]:
        """Healthcheck the agent"""
        is_healthy, data = self.get_agent_health()
        period = data.get("period", None)
        return is_healthy, period

    def get_current_round(self) -> Optional[str]:
        """Get the current round"""
        _, status = self.get_agent_health()

        if "current_round" in status:
            return status["current_round"]

        if "rounds" not in status:
            return None

        if len(status["rounds"]) == 0:
            return None

        return status["rounds"][-1]


class Service:
    """Service"""

    def __init__(self, name: str, agents: List[str], client: PropelClient):
        """Constructor"""
        self.name = name
        self.client = client
        self.agents = {name: Agent(name, client) for name in agents}
        self.not_healthy_counter = 0
        self.last_notification = None
        self.last_restart = None

    def restart(self):
        """Restart the service"""
        logger.info(f"Restarting service {self.name}")
        for agent in self.agents.values():
            agent.restart()

    def stop(self):
        """Stop the service"""
        logger.info(f"Stopping service {self.name}")
        for agent in self.agents.values():
            agent.stop()

    def healthcheck(self) -> bool:
        """Healthcheck the service"""
        logger.info(f"Checking health for service {self.name}")
        alive_threshold = math.floor(len(self.agents) * 2 / 3) + 1
        alive_agents = 0
        for agent in self.agents.values():
            is_agent_healthy, _ = agent.healthcheck()
            if is_agent_healthy:
                alive_agents += 1
        is_service_healthy = alive_agents >= alive_threshold

        if not is_service_healthy:
            self.not_healthy_counter += 1
        else:
            self.not_healthy_counter = 0

        return is_service_healthy


class Propel:
    """Propel"""

    def __init__(self):
        """Constructor"""
        self.client = PropelClient(
            base_url=PROPEL_SERVICE_BASE_URL, credentials_storage=CredentialStorage()
        )

        with open(Path("config.yaml"), "r", encoding="utf-8") as config_file:
            config = yaml.safe_load(config_file)
            self.services = {
                service_name: Service(service_name, agent_names, self.client)
                for service_name, agent_names in config["services"].items()
            }

        self.login()

    def login(self):
        """Login"""
        self.client.login(
            username=os.getenv("PROPEL_USERNAME"),
            password=os.getenv("PROPEL_PASSWORD"),
        )

    def restart_service(self, service_name: str):
        """Restart the service"""
        service = self.services[service_name]
        service.restart()

    def stop_service(self, service_name: str):
        """Stop the service"""
        service = self.services[service_name]
        service.stop()
