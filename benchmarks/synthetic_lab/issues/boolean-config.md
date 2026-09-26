Boolean configuration strings such as "false" and "0" currently enable features.
Fix parse_bool: bool inputs retain their value; None returns the supplied default
(False by default). Strings are trimmed and case-insensitive. true/1/yes/on map
to True; false/0/no/off map to False. Unknown strings, including empty/whitespace
strings, raise ValueError. Other types, including numeric 0/1, raise TypeError.
Preserve other modules and public signatures. Do not modify tests.
