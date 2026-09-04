class DocumentClassifier:


    def classify(self, text):

        text_lower = text.lower()


        if "revenue" in text_lower or "profit" in text_lower:

            return "financial_report"


        if "abstract" in text_lower and "methodology" in text_lower:

            return "research_paper"


        if "agreement" in text_lower or "contract" in text_lower:

            return "legal_document"


        if "invoice" in text_lower:

            return "invoice"


        return "general_document"