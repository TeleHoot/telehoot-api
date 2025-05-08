from typing import Annotated

from fastapi import Depends

from src.app import services

Users = Annotated[services.Users, Depends()]
Organizations = Annotated[services.Organizations, Depends()]
Memberships = Annotated[services.Memberships, Depends()]
Questions = Annotated[services.Questions, Depends()]
Quizzes = Annotated[services.Quizzes, Depends()]
Sessions = Annotated[services.Sessions, Depends()]
Participants = Annotated[services.Participants, Depends()]
ParticipantAnswers = Annotated[services.ParticipantAnswers, Depends()]

Auth = Annotated[services.Authentication, Depends()]
