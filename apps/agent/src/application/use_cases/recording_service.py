"""Recording service use case for orchestrating recording lifecycle."""

from uuid import UUID

import structlog

from src.application.ports import EgressConfig
from src.application.ports import EgressInfo
from src.application.ports import EgressPort
from src.application.ports import EgressStatus
from src.application.ports import RecordingRepositoryPort
from src.application.ports import StoragePort
from src.domain.entities import Recording
from src.domain.entities import RecordingStatus

logger = structlog.get_logger()


class RecordingServiceError(Exception):
    """Base exception for recording service errors."""

    pass


class RecordingNotFoundError(RecordingServiceError):
    """Raised when a recording is not found."""

    pass


class RecordingAlreadyExistsError(RecordingServiceError):
    """Raised when trying to start a recording that already exists."""

    pass


class RecordingService:
    """Orchestrates recording lifecycle.

    This service coordinates between the egress adapter, recording repository,
    and storage adapter to manage the full recording lifecycle.
    """

    def __init__(
        self,
        recording_repository: RecordingRepositoryPort,
        egress_port: EgressPort,
        storage_port: StoragePort,
        default_bucket: str,
        default_width: int = 1280,
        default_height: int = 720,
        default_segment_duration: int = 4,
        presigned_url_expiry: int = 3600,
    ) -> None:
        """Initialize the recording service.

        Args:
            recording_repository: Repository for recording persistence.
            egress_port: Port for LiveKit egress operations.
            storage_port: Port for S3 storage operations.
            default_bucket: Default S3 bucket for recordings.
            default_width: Default video width.
            default_height: Default video height.
            default_segment_duration: Default HLS segment duration.
            presigned_url_expiry: Default presigned URL expiry in seconds.
        """
        self._recording_repo = recording_repository
        self._egress = egress_port
        self._storage = storage_port
        self._default_bucket = default_bucket
        self._default_width = default_width
        self._default_height = default_height
        self._default_segment_duration = default_segment_duration
        self._presigned_url_expiry = presigned_url_expiry

    async def start_recording(
        self,
        session_id: UUID,
        room_name: str,
        bucket: str | None = None,
    ) -> Recording:
        """Start recording for a session.

        Args:
            session_id: The session ID to record.
            room_name: The LiveKit room name.
            bucket: Optional S3 bucket (uses default if not specified).

        Returns:
            The created Recording entity.

        Raises:
            RecordingAlreadyExistsError: If recording already exists for session.
            RecordingServiceError: If starting the recording fails.
        """
        # Check for existing recording
        existing = await self._recording_repo.get_by_session_id(session_id)
        if existing and not existing.is_terminal:
            raise RecordingAlreadyExistsError(
                f"Active recording already exists for session {session_id}"
            )

        bucket = bucket or self._default_bucket
        storage_path = f"recordings/{session_id}"

        # Create recording entity in STARTING state
        recording = Recording(
            session_id=session_id,
            egress_id="pending",  # Will be updated after egress starts
            storage_bucket=bucket,
            storage_path=storage_path,
        )

        logger.info(
            "starting_recording",
            recording_id=str(recording.id),
            session_id=str(session_id),
            room_name=room_name,
        )

        try:
            # Start egress
            egress_config = EgressConfig(
                room_name=room_name,
                output_bucket=bucket,
                output_path=storage_path,
                width=self._default_width,
                height=self._default_height,
                segment_duration=self._default_segment_duration,
            )
            egress_info = await self._egress.start_room_composite(egress_config)

            # Update recording with egress ID
            recording.egress_id = egress_info.egress_id

            # Save recording
            await self._recording_repo.save(recording)

            logger.info(
                "recording_started",
                recording_id=str(recording.id),
                egress_id=egress_info.egress_id,
            )

            return recording

        except Exception as e:
            # Mark recording as failed
            recording.fail(str(e))
            await self._recording_repo.save(recording)
            logger.error(
                "recording_start_failed",
                recording_id=str(recording.id),
                error=str(e),
            )
            raise RecordingServiceError(f"Failed to start recording: {e}") from e

    async def stop_recording(self, session_id: UUID) -> Recording:
        """Stop recording for a session.

        Args:
            session_id: The session ID to stop recording.

        Returns:
            The updated Recording entity.

        Raises:
            RecordingNotFoundError: If no active recording found.
            RecordingServiceError: If stopping the recording fails.
        """
        recording = await self._recording_repo.get_by_session_id(session_id)
        if recording is None:
            raise RecordingNotFoundError(f"No recording found for session {session_id}")

        if recording.is_terminal:
            logger.warning(
                "recording_already_stopped",
                recording_id=str(recording.id),
                status=recording.status.value,
            )
            return recording

        logger.info(
            "stopping_recording",
            recording_id=str(recording.id),
            session_id=str(session_id),
        )

        try:
            # Handle STARTING state - egress never started, fail the recording
            if recording.status == RecordingStatus.STARTING:
                recording.fail("Recording stopped before egress started")
                await self._recording_repo.save(recording)
                logger.info(
                    "recording_failed_before_start",
                    recording_id=str(recording.id),
                )
                return recording

            # Stop egress
            await self._egress.stop_egress(recording.egress_id)

            # Transition to processing state
            recording.start_processing()
            await self._recording_repo.save(recording)

            logger.info(
                "recording_stopped",
                recording_id=str(recording.id),
                status=recording.status.value,
            )

            return recording

        except Exception as e:
            logger.error(
                "recording_stop_failed",
                recording_id=str(recording.id),
                error=str(e),
            )
            raise RecordingServiceError(f"Failed to stop recording: {e}") from e

    async def handle_egress_event(self, egress_info: EgressInfo) -> Recording | None:
        """Handle egress webhook events.

        Args:
            egress_info: Information from egress event.

        Returns:
            Updated Recording entity, or None if not found.
        """
        recording = await self._recording_repo.get_by_egress_id(egress_info.egress_id)
        if recording is None:
            logger.warning(
                "recording_not_found_for_egress",
                egress_id=egress_info.egress_id,
            )
            return None

        logger.info(
            "handling_egress_event",
            recording_id=str(recording.id),
            egress_id=egress_info.egress_id,
            egress_status=egress_info.status.value,
        )

        try:
            if egress_info.status == EgressStatus.ACTIVE:
                # Egress has started
                if recording.status == RecordingStatus.STARTING:
                    recording.activate()
                    await self._recording_repo.save(recording)

            elif egress_info.status == EgressStatus.COMPLETE:
                # Egress completed - get file info and complete recording
                await self._complete_recording(recording, egress_info)

            elif egress_info.status == EgressStatus.FAILED:
                # Egress failed
                error_msg = egress_info.error or "Unknown egress error"
                recording.fail(error_msg)
                await self._recording_repo.save(recording)
                logger.error(
                    "egress_failed",
                    recording_id=str(recording.id),
                    error=error_msg,
                )

            return recording

        except Exception as e:
            logger.error(
                "egress_event_handling_failed",
                recording_id=str(recording.id),
                error=str(e),
            )
            recording.fail(str(e))
            await self._recording_repo.save(recording)
            return recording

    async def _complete_recording(
        self,
        recording: Recording,
        egress_info: EgressInfo,
    ) -> None:
        """Complete a recording after egress finishes.

        Args:
            recording: The recording to complete.
            egress_info: Egress completion information with duration and file size.
        """
        # Ensure recording is in processing state
        if recording.status == RecordingStatus.ACTIVE:
            recording.start_processing()

        # Get playlist URL
        playlist_key = f"{recording.storage_path}/index.m3u8"
        playlist_url = await self._storage.generate_presigned_url(
            bucket=recording.storage_bucket,
            key=playlist_key,
            expiry_seconds=self._presigned_url_expiry,
        )

        # Use egress_info values if available, fallback to storage lookup
        duration_seconds = egress_info.duration_seconds or 0
        file_size = egress_info.file_size_bytes

        if file_size is None:
            # Fallback: get file size from storage if not in egress_info
            obj_info = await self._storage.get_object_info(
                bucket=recording.storage_bucket,
                key=playlist_key,
            )
            file_size = obj_info.size_bytes if obj_info else 0

        recording.complete(
            playlist_url=playlist_url,
            duration_seconds=duration_seconds,
            file_size_bytes=file_size,
        )
        await self._recording_repo.save(recording)

        logger.info(
            "recording_completed",
            recording_id=str(recording.id),
            playlist_url=playlist_url,
            duration_seconds=duration_seconds,
            file_size_bytes=file_size,
        )

    async def get_playback_url(
        self,
        recording_id: UUID,
        expiry_seconds: int | None = None,
    ) -> str:
        """Generate presigned URL for playback.

        Args:
            recording_id: The recording ID.
            expiry_seconds: Optional URL expiry time.

        Returns:
            Presigned URL for the HLS playlist.

        Raises:
            RecordingNotFoundError: If recording not found.
            RecordingServiceError: If recording is not completed.
        """
        recording = await self._recording_repo.get_by_id(recording_id)
        if recording is None:
            raise RecordingNotFoundError(f"Recording {recording_id} not found")

        if recording.status != RecordingStatus.COMPLETED:
            raise RecordingServiceError(
                f"Recording {recording_id} is not completed (status: {recording.status.value})"
            )

        expiry = expiry_seconds or self._presigned_url_expiry
        playlist_key = f"{recording.storage_path}/index.m3u8"

        url = await self._storage.generate_presigned_url(
            bucket=recording.storage_bucket,
            key=playlist_key,
            expiry_seconds=expiry,
        )

        logger.debug(
            "playback_url_generated",
            recording_id=str(recording_id),
            expiry_seconds=expiry,
        )

        return url

    async def get_recording(self, recording_id: UUID) -> Recording | None:
        """Get a recording by ID.

        Args:
            recording_id: The recording ID.

        Returns:
            The recording if found, None otherwise.
        """
        return await self._recording_repo.get_by_id(recording_id)

    async def get_recording_by_session(self, session_id: UUID) -> Recording | None:
        """Get a recording by session ID.

        Args:
            session_id: The session ID.

        Returns:
            The recording if found, None otherwise.
        """
        return await self._recording_repo.get_by_session_id(session_id)
