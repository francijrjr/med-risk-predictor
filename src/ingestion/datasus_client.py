"""Reserved integration boundary; no automatic fallback to invented records."""


class DataSUSClient:
    def fetch_medication_data(self, params):
        raise NotImplementedError(
            "Integração DATASUS pendente de seleção de base, extração e validação. "
            "Utilize históricos municipais em CSV para a análise."
        )
