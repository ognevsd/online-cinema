class ElasticSearchClientException(Exception):
    pass


class BulkUploadFailed(ElasticSearchClientException):
    """Используется когда есть ошибка в Bulk загрузке данных"""

    def __init__(self, *args: object) -> None:
        super().__init__(*args)
