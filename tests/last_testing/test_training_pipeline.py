from om_ai.training_pipeline import (

    ExperienceCollector,

    DatasetManager,

    SFTGenerator,

    TrainingPipeline

)



collector = ExperienceCollector()


experience = collector.create(

    "Build restaurant management system",

    "Created Laravel architecture",

    {

        "category":

        "software"

    }

)



sft = SFTGenerator().create(

    experience

)



dataset = DatasetManager()


dataset.add(

    sft

)



trainer = TrainingPipeline()


print(

    trainer.prepare(

        dataset.load()

    )

)