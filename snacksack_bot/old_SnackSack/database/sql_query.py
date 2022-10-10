import re


class SqlQuery:
    def __init__(self, text: str, **kwargs):
        self.__text: str = text
        self.__kwargs: dict = kwargs

    @property
    def text(self) -> str:
        """Returns SQL-query text as if you've put all the values into prepared
        SQL-query.
        """
        query_text = self.__text

        for key, value in self.__kwargs.items():
            query_text = re.sub(f":{key}", f"{value}", query_text)

        return query_text

    def __call__(self) -> tuple:
        """Returns tuple, containing prepared SQL-query and values to put into
        it.
        """
        query_text = self.__text

        i = 1
        for key in self.__kwargs.keys():
            query_text = re.sub(f":{key}", f"${i}", query_text)
            i += 1

        return (query_text, *self.__kwargs.values())
