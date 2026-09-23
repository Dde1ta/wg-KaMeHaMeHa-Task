import re


class Item:
    def __init__(self):
        self._attacker = {}
        self._defender = {}
        self._location = ""
        self._time = 0
        self._result = False  # boolean
        self._reason = ""
        self._damage = 0

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
    def reason(self) -> str:
        return self._reason

    @property
    def damage(self) -> int:
        return self._damage

    @attacker.setter
    def attacker(self, value: str) -> None:
        """
            Sets the attacker and their class
        :param value: value of the dynamodb item Expected <class>#<name>
        :return: None
        """

        regex = r"^([a-zA-Z0-9_]+)#([a-zA-Z0-9_]+)$"

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

        regex = r"^([a-zA-Z0-9_]+)#([a-zA-Z0-9_]+)$"

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

    @reason.setter
    def reason(self, value: str) -> None:

        regex = r"(.+)$"

        match = self.validate_field(regex, value)

        if match is not None:
            self._reason = value
        else:
            raise ValueError("Reason is wrongly formatted")

    @damage.setter
    def damage(self, value: int) -> None:

        # \d+ checks for one or more digits
        regex = r"^\d+$"

        match = self.validate_field(regex, str(value))

        if match is not None:
            self._damage = value
        else:
            raise ValueError("Damage is wrongly formatted")

    @classmethod
    def validate_field(cls, regex: str, value: str) -> re.Match | None:
        match = re.fullmatch(regex, value)

        if match:
            return match
        else:
            return None

    def to_dict(self) -> dict:
        return {
            "Attacker": self.attacker,
            "Defender": self.defender,
            "Location": self.location,
            "Result":  "Successful" if self.result else "Failed",
            "Timestamp": self.timestamp,
            "Reason for attack": self.reason,
            "Damage": self.damage
        }
