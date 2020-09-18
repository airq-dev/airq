import datetime
import enum
import logging
import pytz
import typing

from sqlalchemy import func
from sqlalchemy.orm import joinedload
from sqlalchemy.orm import Query
from twilio.base.exceptions import TwilioRestException

from airq.config import db
from airq.lib.readings import Pm25
from airq.lib.readings import pm25_to_aqi
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
    last_activity_at = db.Column(
        db.Integer(), nullable=False, index=True, server_default="0"
    )

    zipcode_id = db.Column(
        db.Integer(),
        db.ForeignKey("zipcodes.id", name="clients_zipcode_id_fkey"),
        nullable=True,
    )
    last_pm25 = db.Column(db.Float(), nullable=True)
    last_alert_sent_at = db.Column(
        db.Integer(), nullable=False, index=True, server_default="0"
    )
    alerts_disabled_at = db.Column(
        db.Integer(), nullable=False, index=True, server_default="0"
    )
    num_alerts_sent = db.Column(db.Integer(), nullable=False, server_default="0")

    requests = db.relationship("Request")
    zipcode = db.relationship("Zipcode")

    __table_args__ = (
        db.Index(
            "_client_identifier_type_code", "identifier", "type_code", unique=True,
        ),
    )

    # Send alerts at most every one hour to avoid spamming people.
    # One hour seems like a reasonable frequency because AQI
    # doesn't fluctuate very frequently. We should look at implementing
    # logic to smooth out this alerting so that if AQI oscillates
    # between two levels we don't spam the user every hour.
    FREQUENCY = 1 * 60 * 60

    # Send alerts between 8 AM and 9 PM.
    SEND_WINDOW_HOURS = (8, 21)

    @classmethod
    def curr_ts(cls) -> int:
        return int(datetime.datetime.now().timestamp())

    #
    # Presence
    #

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

    def mark_seen(self):
        self.last_activity_at = self.curr_ts()
        db.session.commit()

    #
    # Alerting
    #

    @property
    def is_enabled_for_alerts(self) -> bool:
        return bool(self.zipcode_id and not self.alerts_disabled_at)

    def update_subscription(self, zipcode: Zipcode) -> bool:
        self.last_pm25 = zipcode.pm25
        curr_zipcode_id = self.zipcode_id
        if curr_zipcode_id != zipcode.id:
            # TODO: Command to re-enable alerts instead of auto re-enabling them.
            self.alerts_disabled_at = 0
            self.zipcode_id = zipcode.id
        db.session.commit()
        return curr_zipcode_id != self.zipcode_id

    def disable_alerts(self):
        self.last_pm25 = None
        self.alerts_disabled_at = self.curr_ts()
        db.session.commit()

    @property
    def is_in_send_window(self) -> bool:
        if self.zipcode_id is None:
            return False
        # Timezone can be null since our data is incomplete.
        timezone = self.zipcode.timezone or "America/Los_Angeles"
        dt = datetime.datetime.now(tz=pytz.timezone(timezone))
        send_start, send_end = self.SEND_WINDOW_HOURS
        return send_start <= dt.hour < send_end

    def send_message(self, message: str) -> bool:
        if self.type_code == ClientIdentifierType.PHONE_NUMBER:
            try:
                send_sms(message, self.identifier)
            except TwilioRestException as e:
                if e.code == 21610:
                    # The message From/To pair violates a blacklist rule.
                    logger.warning(
                        "Disabling alerts for unsubscribed recipient %s", self
                    )
                    self.disable_alerts()
                    return False
                else:
                    raise
        else:
            # Other clients types don't yet support message sending.
            logger.info("Not messaging client %s: %s", self.id, message)

        return True

    def maybe_notify(self) -> bool:
        if not self.is_in_send_window:
            return False

        curr_pm25 = self.zipcode.pm25
        curr_aqi_level = Pm25.from_measurement(curr_pm25)
        curr_aqi = pm25_to_aqi(curr_pm25)

        # Only send if the pm25 changed a level since the last time we sent this alert.
        last_aqi_level = Pm25.from_measurement(self.last_pm25)
        last_aqi = pm25_to_aqi(self.last_pm25)
        if curr_aqi_level == last_aqi_level:
            return False

        message = (
            "Air quality in {city} {zipcode} has changed to {curr_aqi_level} (AQI {curr_aqi})"
        ).format(
            city=self.zipcode.city.name,
            zipcode=self.zipcode.zipcode,
            curr_aqi_level=curr_aqi_level.display,
            curr_aqi=curr_aqi,
        )
        if not self.send_message(message):
            return False

        self.last_alert_sent_at = self.curr_ts()
        self.last_pm25 = curr_pm25
        self.num_alerts_sent += 1
        db.session.commit()

        return True

    #
    # Fetchers
    #

    @classmethod
    def get_or_create(
        cls, identifier: str, type_code: ClientIdentifierType
    ) -> typing.Tuple["Client", bool]:
        client = cls.query.filter_by(identifier=identifier, type_code=type_code).first()
        if not client:
            client = cls(
                identifier=identifier,
                type_code=type_code,
                last_activity_at=datetime.datetime.now().timestamp(),
            )
            db.session.add(client)
            db.session.commit()
            was_created = True
        else:
            was_created = False
        return client, was_created

    @classmethod
    def get_by_phone_number(cls, phone_number: str) -> typing.Optional["Client"]:
        if len(phone_number) == 10:
            phone_number = "1" + phone_number
        if len(phone_number) == 11:
            phone_number = "+" + phone_number
        return cls.filter_phones().filter_by(identifier=phone_number).first()

    #
    # Filters
    #

    @classmethod
    def filter_phones(cls) -> Query:
        return cls.query.filter(cls.type_code == ClientIdentifierType.PHONE_NUMBER)

    @classmethod
    def filter_inactive_since(cls, timestamp: float) -> Query:
        return (
            cls.filter_phones()
            .filter(cls.last_activity_at < timestamp)
            .filter(cls.last_alert_sent_at < timestamp)
        )

    @classmethod
    def filter_eligible_for_sending(cls) -> Query:
        cutoff = cls.curr_ts() - cls.FREQUENCY
        return (
            cls.filter_phones()
            .options(joinedload(cls.zipcode))
            .filter(cls.alerts_disabled_at == 0)
            .filter(cls.last_alert_sent_at < cutoff)
            .filter(cls.zipcode_id.isnot(None))
        )

    #
    # Stats
    #

    @classmethod
    def get_total_num_sends(cls) -> int:
        return (
            cls.filter_phones().with_entities(func.sum(cls.num_alerts_sent)).scalar()
            or 0
        )

    @classmethod
    def get_total_num_subscriptions(cls) -> int:
        return (
            cls.filter_phones()
            .filter(cls.alerts_disabled_at == 0)
            .filter(cls.zipcode_id.isnot(None))
            .count()
        )

    @classmethod
    def get_activity_counts(cls):
        windows = [1, 2, 3, 4, 5, 6, 7, 30]
        curr_time = cls.curr_ts()
        counts = {window: 0 for window in windows}
        for client in cls.filter_phones().all():
            for window in windows:
                ts = curr_time - (window * 24 * 60 * 60)
                if client.last_activity_at > ts or client.last_alert_sent_at > ts:
                    counts[window] += 1
        return counts
