import re


class Item:
    def __init__(self):
        self._attacker = {}
        self._defender = {}
        self._location = ""
        self._time = 0
        self._attack_id = ""
        self._result = False  # boolean

    @property
    def attacker(self) -> dict:
        """
            getter for attacker
        :return: dictionary containing {"class" : <class>, "name": <name>}
        """
        return self._attacker

    @property
    def defender(self) -> dict:
        """
            getter for defender
        :return: dictionary containing {"class" : <class>, "name": <name>}
        """
        return self._defender

    @property
    def location(self) -> str:
        return self._location

    @property
    def timestamp(self) -> int:
        return self._time

    @property
    def result(self) -> bool:
        return self._result

    @property
    def attack_id(self) -> str:
        return self._attack_id

    @attacker.setter
    def attacker(self, value: str) -> None:
        """
            Sets the attacker and their class
        :param value: value of the dynamodb item Expected <class>#<name>
        :return: None
        """

        regex = r"^([a-zA-Z_]+)#([a-zA-Z_]+)$"

        match = self.validate_field(regex, value)

        if match is not None:
            self._attacker = {
                "class": match.group(1),
                "name": match.group(2)
            }
        else:
            raise ValueError("Attacker is wrongly formatted")

    @defender.setter
    def defender(self, value: str) -> None:
        """
            Sets the defender and their class
        :param value: value of the dynamodb item Expected <class>#<name>
        :return: None
        """

        regex = r"^([a-zA-Z_]+)#([a-zA-Z_]+)$"

        match = self.validate_field(regex, value)

        if match is not None:
            self._defender = {
                "class": match.group(1),
                "name": match.group(2)
            }
        else:
            raise ValueError("Defender is wrongly formatted")

    @location.setter
    def location(self, value: str) -> None:

        regex = "(.+)$"

        match = self.validate_field(regex, value)

        if match is not None:
            self._location = value
        else:
            raise ValueError("location is wrongly formatted")

    @timestamp.setter
    def timestamp(self, value: int) -> None:

        regex = r"^(\d{10}|\d{13})$"

        match = self.validate_field(regex, str(value))

        if match is not None:
            self._time = value
        else:
            raise ValueError("timestamp is wrongly formatted")

    @result.setter
    def result(self, value: bool) -> None:
        if isinstance(value, bool):
            self._result = value
        else:
            raise ValueError("Result has to be boolean")

    @attack_id.setter
    def attack_id(self, value: str) -> None:
        """
        uuid 7
        :param value:
        :return:
        """
        regex = r'^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-7[0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$'

        match = self.validate_field(regex, str(value))

        if match is not None:
            self._attack_id = value
        else:
            raise ValueError("attack_id is wrongly formatted")

    def to_dict(self) -> dict:
        return {
            "AttackID": self.attack_id,
            "Attacker": self.attacker,
            "Defender": self.defender,
            "Location": self.location,
            "Result":  "Successful" if self.result else "Failed",
            "Timestamp": self.timestamp
        }

    @classmethod
    def validate_field(cls, regex: str, value: str) -> re.Match | None:
        match = re.fullmatch(regex, value)

        if match:
            return match
        else:
            return None
