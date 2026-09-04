class QualityChecker:


    def check(self, response):


        return {

            "valid":
                bool(response.strip()),

            "length":
                len(response)

        }