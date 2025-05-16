from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status

from src import core
from src.app import api, models, schemas, services

ws_manager = core.websockets.get_websocket_manager()


@ws_manager.router.on(schemas.sessions.SessionEventType.ANSWER)
async def handle_answer(
    websocket: WebSocket,
    connection_id: UUID,
    session_id: UUID,
    data: dict,
    user: schemas.users.Read,
):
    if not data["text"]:
        await ws_manager.send_event_to_connection(
            connection_id,
            schemas.sessions.ErrorEvent(
                error_code="unsupported_data",
                message="Text of answer not included",
                code=status.WS_1003_UNSUPPORTED_DATA,
            ),
        )

    sessions_service = services.Sessions()
    participants_service = services.Participants()
    participant_answers_service = services.ParticipantAnswers()
    questions_service = services.Questions()

    uow_factory = api.dependencies.uow.get_uow_factory(use_postgres=True, use_mongodb=True)

    async for uow in uow_factory():
        try:
            session = await sessions_service.read_by_id(uow, session_id)
        except core.services.exceptions.EntityNotFoundError as e:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="entity_not_found",
                    message="Session not found",
                    code=status.WS_1003_UNSUPPORTED_DATA,
                ),
            )
            raise WebSocketDisconnect from e

        if session.status != models.session.SessionStatus.ACTIVE:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="invalid_session_status",
                    message="Session must be in ACTIVE status",
                    code=status.WS_1008_POLICY_VIOLATION,
                ),
            )

        participant = await participants_service.read_many(
            uow, filters=schemas.participants.Filters(user_id=user.id, session_id=session_id)
        )

        if not participant:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="entity_not_found",
                    message="Participant not found",
                    code=status.WS_1003_UNSUPPORTED_DATA,
                ),
            )
            raise WebSocketDisconnect

        participant = participant[0]

        if participant.role == models.ParticipantRole.HOST:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="invalid_user_role",
                    message="To start session user must be participant",
                    code=status.WS_1008_POLICY_VIOLATION,
                ),
            )
            raise WebSocketDisconnect

        try:
            questions = await questions_service.read_many(
                uow,
                filters=schemas.questions.Filters(quiz_id=session.quiz.id),
                sorting=schemas.questions.SortParams(sort_by=schemas.questions.SortFields.ORDER),
            )
            question = questions[session.current_question_index]

            correct_answers = {
                answer.text.lower() for answer in question.answers if answer.is_correct
            }
            participant_answers = {ans.lower() for ans in data["answers"]}
            is_correct = correct_answers == participant_answers

            answers = await participant_answers_service.read_many(
                uow,
                filters=schemas.participant_answers.Filters(question_id=str(question.id)),
            )

            if answers:
                await participant_answers_service.update_by_id(
                    uow,
                    answers[0].id,
                    schemas.participant_answers.Update(
                        text=data["text"],
                        is_correct=is_correct,
                        points=question.weight if is_correct else 0,
                    ),
                )
            else:
                await participant_answers_service.create(
                    uow,
                    schemas.participant_answers.Create(
                        text=data["text"],
                        is_correct=is_correct,
                        points=question.weight if is_correct else 0,
                        participant_id=participant.id,
                        question_id=str(question.id),
                    ),
                )

        except Exception as e:
            await ws_manager.send_event_to_connection(
                connection_id,
                schemas.sessions.ErrorEvent(
                    error_code="internal_server_error",
                    message=str(e),
                    code=status.WS_1011_INTERNAL_ERROR,
                ),
            )
            raise WebSocketDisconnect from e

        event = schemas.sessions.SessionAnsweredEvent()

        await ws_manager.broadcast_event_to_channel(str(session_id), event)
