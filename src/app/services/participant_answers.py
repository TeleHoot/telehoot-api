from src import core
from src.app import models, repositories, schemas


class ParticipantAnswers(
    core.services.BaseCRUD[
        schemas.participant_answers.Create,
        schemas.participant_answers.Read,
        schemas.participant_answers.Update,
        schemas.participant_answers.Filters,
        schemas.participant_answers.SortParams,
        models.ParticipantAnswer,
    ]
):
    def __init__(self):
        self.repo = repositories.ParticipantAnswers()
        super().__init__(
            repo=self.repo,
            create_schema=schemas.participant_answers.Create,
            read_schema=schemas.participant_answers.Read,
            update_schema=schemas.participant_answers.Update,
            filters_schema=schemas.participant_answers.Filters,
        )
