import json
from typing import List, Optional

import jsonpickle

from cyberwheel.agents.red.atomic_test import AtomicTest


class Technique:
    """Defines a class representing a MITRE ATT&CK technique.

    Attributes:
        mitre_id (str): The MITRE ATT&CK ID of the technique.
        name (str): The name of the technique.
        technique_id (str): The technique identifier.
        data_components (List[str]): List of data components related to the technique.
        kill_chain_phases (List[str]): List of kill chain phases associated with the technique.
        data_source_platforms (List[str]): List of data source platforms supporting the technique.
        mitigations (List[str]): List of mitigations associated with the technique.
        description (str): The description of the technique.
        atomic_tests (List[AtomicTest]): List of atomic tests for the technique.
        cwe_list (List[str]): List of Common Weakness Enumeration (CWE) identifiers.
        cve_list (List[str]): List of Common Vulnerabilities and Exposures (CVE) identifiers.
        is_subtechnique (bool): Flag indicating if the technique is a sub-technique.
        parent_technique (str): The parent technique ID if the technique is a sub-technique.
        supported_os (List[str]): List of supported operating systems.
    """

    def __init__(
        self,
        mitre_id: str,
        name: str,
        technique_id: str,
        data_components: List[str],
        kill_chain_phases: List[str],
        data_source_platforms: List[str],
        mitigations: List[str],
        description: bytes,
        atomic_tests: List[dict],
        cve_list: Optional[List[str]] = None,
        cwe_list: Optional[List[str]] = None,
    ) -> None:
        """Initialize a Technique object.

        Args:
            mitre_id (str): The MITRE ATT&CK ID of the technique.
            name (str): The name of the technique.
            technique_id (str): The technique identifier.
            data_components (List[str]): List of data components related to the technique.
            kill_chain_phases (List[str]): List of kill chain phases associated with the technique.
            data_source_platforms (List[str]): List of data source platforms supporting the technique.
            mitigations (List[str]): List of mitigations associated with the technique.
            description (bytes): The description of the technique in byte format.
            atomic_tests (List[dict]): List of atomic tests for the technique.
            cve_list (Optional[List[str]]): List of Common Vulnerabilities and Exposures (CVE) identifiers. Default is None.
            cwe_list (Optional[List[str]]): List of Common Weakness Enumeration (CWE) identifiers. Default is None.
        """
        self.mitre_id = mitre_id
        self.name = name
        self.technique_id = technique_id
        self.data_components = data_components
        self.kill_chain_phases = kill_chain_phases
        self.data_source_platforms = data_source_platforms
        self.mitigations = mitigations
        self.description = description.decode(
            'utf-8')  # Decode bytes to string
        self.atomic_tests = [AtomicTest(at) for at in atomic_tests
                             ]  # Initialize AtomicTest objects from dicts
        self.is_subtechnique = ('.' in self.mitre_id
                                )  # Check if the technique is a sub-technique
        self.parent_technique = (self.mitre_id.split('.')[0]
                                 if self.is_subtechnique else self.mitre_id)
        self.supported_os = list(
            set(os for at in self.atomic_tests
                for os in at.supported_platforms))
        self.cwe_list = cwe_list or []  # Initialize to empty list if None
        self.cve_list = cve_list or []  # Initialize to empty list if None

    def get_parent_technique(self) -> str:
        """Get the parent technique ID.

        Returns:
            str: The parent technique ID.
        """
        return self.parent_technique

    def get_vulnerabilities(self) -> List[str]:
        """Get the list of CVEs associated with the technique.

        Returns:
            List[str]: List of CVE identifiers.
        """
        return self.cve_list

    def get_weaknesses(self) -> List[str]:
        """Get the list of CWEs associated with the technique.

        Returns:
            List[str]: List of CWE identifiers.
        """
        return self.cwe_list

    def __str__(self) -> str:
        """Convert the Technique object to a JSON string.

        Returns:
            str: JSON string representation of the Technique object.
        """
        obj = jsonpickle.encode(self)  # Serialize object to JSON
        return json.dumps(json.loads(obj), indent=4)  # Pretty-print JSON
