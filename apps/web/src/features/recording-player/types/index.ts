// Recording status enum matching backend
export type RecordingStatus = "starting" | "active" | "processing" | "completed" | "failed";

// Transcript message matching backend contract
export interface TranscriptMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestampMs: number;
}

// Recording summary for list view
export interface RecordingSummary {
  id: string;
  sessionId: string;
  status: RecordingStatus;
  durationSeconds: number | null;
  createdAt: string;
  playbackUrl: string | null;
}

// Recording detail for playback view
export interface RecordingDetail {
  id: string;
  sessionId: string;
  status: RecordingStatus;
  durationSeconds: number | null;
  fileSizeBytes: number | null;
  createdAt: string;
  startedAt: string | null;
  endedAt: string | null;
  playbackUrl: string | null;
  transcript: TranscriptMessage[];
}

// API response types
export interface RecordingListResponse {
  recordings: RecordingSummary[];
  total: number;
  page: number;
  pageSize: number;
}

export type RecordingDetailResponse = RecordingDetail;

// Component prop types
export interface VideoPlayerProps {
  src: string | null;
  onTimeUpdate?: (currentTime: number) => void;
  onDurationChange?: (duration: number) => void;
  onError?: (error: Error) => void;
  className?: string;
}

export interface SyncedTranscriptProps {
  transcript: TranscriptMessage[];
  currentTimeMs: number;
  onSeek?: (timestampMs: number) => void;
  className?: string;
}

export interface PlaybackViewProps {
  recordingId: string;
}

export interface RecordingListProps {
  page?: number;
  pageSize?: number;
}
