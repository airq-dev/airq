import datetime
import enum
import logging
import typing

from airq.config import db
from airq.lib.twilio import send_sms
from airq.models.requests import Request
from airq.models.zipcodes import Zipcode


logger = logging.getLogger(__name__)


class ClientIdentifierType(enum.Enum):
    PHONE_NUMBER = 1
    IP = 2


class Client(db.Model):  # type: ignore
    __tablename__ = "clients"

    id = db.Column(db.Integer(), primary_key=True)
    identifier = db.Column(db.String(), nullable=False)
    type_code = db.Column(db.Enum(ClientIdentifierType), nullable=False)

    requests = db.relationship("Request")

    __table_args__ = (
        db.Index(
            "_client_identifier_type_code", "identifier", "type_code", unique=True,
        ),
    )

    @classmethod
    def get_or_create(
        cls, identifier: str, type_code: ClientIdentifierType
    ) -> "Client":
        client = cls.query.filter_by(identifier=identifier, type_code=type_code).first()
        if not client:
            client = cls(identifier=identifier, type_code=type_code)
            db.session.add(client)
            db.session.commit()
        return client

    def get_last_requested_zipcode(self) -> typing.Optional[Zipcode]:
        return (
            Zipcode.query.join(Request)
            .filter(Request.client_id == self.id)
            .order_by(Request.last_ts.desc())
            .first()
        )

    def log_request(self, zipcode: Zipcode):
        request = Request.query.filter_by(
            client_id=self.id, zipcode_id=zipcode.id,
        ).first()
        now = datetime.datetime.now().timestamp()
        if request is None:
            request = Request(
                client_id=self.id,
                zipcode_id=zipcode.id,
                count=1,
                first_ts=now,
                last_ts=now,
            )
            db.session.add(request)
        else:
            request.count += 1
            request.last_ts = now
        db.session.commit()

    def send_message(self, message: str):
        if self.type_code == ClientIdentifierType.PHONE_NUMBER:
            send_sms(message, self.identifier)
        else:
            # Other clients types don't yet support message sending.
            logger.info("Not messaging client %s: %s", self.id, message)

    def update_subscription(self, zipcode_id: int, current_pm25: float) -> bool:
        from airq.models.subscriptions import Subscription

        current_subscription = Subscription.query.filter_by(
            client_id=self.id, disabled_at=0
        ).first()
        if current_subscription:
            if current_subscription.zipcode_id == zipcode_id:
                return False
            current_subscription.disable()

        subscription = Subscription.get_or_create(self.id, zipcode_id)
        if subscription.is_disabled:
            subscription.enable()

        # This is a new subscription
        # Mark it to be checked again in 3 hours.
        subscription.last_pm25 = current_pm25
        subscription.last_executed_at = datetime.datetime.now().timestamp()
        db.session.add(subscription)
        db.session.commit()

        return True
