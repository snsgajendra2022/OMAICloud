class DatasetGenerator:



    def generate(
        self,
        records
    ):


        dataset=[]


        for record in records:


            dataset.append({

                "instruction":
                    record.input_data,


                "response":
                    record.output_data,


                "feedback":
                    record.feedback

            })


        return dataset