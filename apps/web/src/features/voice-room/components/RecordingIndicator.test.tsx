import { act, renderHook } from "@testing-library/react";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { render } from "@/test/utils";

import { RecordingIndicator, type RecordingState, useRecordingState } from "./RecordingIndicator";

describe("RecordingIndicator", () => {
  describe("duration formatting", () => {
    it("formats 0 seconds as 00:00", () => {
      render(<RecordingIndicator state="recording" durationSeconds={0} />);

      expect(screen.getByText("Recording 00:00")).toBeInTheDocument();
    });

    it("formats 65 seconds as 01:05", () => {
      render(<RecordingIndicator state="recording" durationSeconds={65} />);

      expect(screen.getByText("Recording 01:05")).toBeInTheDocument();
    });

    it("formats 3661 seconds as 61:01", () => {
      render(<RecordingIndicator state="recording" durationSeconds={3661} />);

      expect(screen.getByText("Recording 61:01")).toBeInTheDocument();
    });
  });

  describe("state rendering", () => {
    it("renders idle state with 'Not Recording'", () => {
      render(<RecordingIndicator state="idle" />);

      expect(screen.getByText("Not Recording")).toBeInTheDocument();
    });

    it("renders recording state with duration", () => {
      render(<RecordingIndicator state="recording" durationSeconds={120} />);

      expect(screen.getByText("Recording 02:00")).toBeInTheDocument();
    });

    it("renders starting state with 'Starting...'", () => {
      render(<RecordingIndicator state="starting" />);

      expect(screen.getByText("Starting...")).toBeInTheDocument();
    });

    it("renders stopping state with 'Stopping...'", () => {
      render(<RecordingIndicator state="stopping" />);

      expect(screen.getByText("Stopping...")).toBeInTheDocument();
    });

    it("renders stopped state with 'Recording Stopped'", () => {
      render(<RecordingIndicator state="stopped" />);

      expect(screen.getByText("Recording Stopped")).toBeInTheDocument();
    });

    it("renders error state with 'Recording Error'", () => {
      render(<RecordingIndicator state="error" />);

      expect(screen.getByText("Recording Error")).toBeInTheDocument();
    });
  });

  describe("toggle button", () => {
    it("renders button when onToggle is provided", () => {
      const onToggle = vi.fn();
      render(<RecordingIndicator state="idle" onToggle={onToggle} />);

      expect(screen.getByRole("button")).toBeInTheDocument();
    });

    it("renders span when onToggle is not provided", () => {
      render(<RecordingIndicator state="idle" />);

      expect(screen.queryByRole("button")).not.toBeInTheDocument();
      expect(screen.getByText("Not Recording")).toBeInTheDocument();
    });

    it("calls onToggle when button is clicked", async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<RecordingIndicator state="idle" onToggle={onToggle} />);

      await user.click(screen.getByRole("button"));

      expect(onToggle).toHaveBeenCalledTimes(1);
    });

    it("does not call onToggle when disabled", async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<RecordingIndicator state="idle" onToggle={onToggle} disabled />);

      await user.click(screen.getByRole("button"));

      expect(onToggle).not.toHaveBeenCalled();
    });

    it("disables button during transitioning states", () => {
      const onToggle = vi.fn();
      render(<RecordingIndicator state="starting" onToggle={onToggle} />);

      const button = screen.getByRole("button");
      expect(button).toBeDisabled();
    });

    it("enables button when not transitioning", () => {
      const onToggle = vi.fn();
      render(<RecordingIndicator state="idle" onToggle={onToggle} />);

      const button = screen.getByRole("button");
      expect(button).not.toBeDisabled();
    });
  });

  describe("hover behavior", () => {
    it("shows 'Start Recording' on hover when idle", async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<RecordingIndicator state="idle" onToggle={onToggle} />);

      const button = screen.getByRole("button");
      await user.hover(button);

      expect(screen.getByText("Start Recording")).toBeInTheDocument();
    });

    it("shows 'Stop Recording' on hover when recording", async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<RecordingIndicator state="recording" onToggle={onToggle} />);

      const button = screen.getByRole("button");
      await user.hover(button);

      expect(screen.getByText("Stop Recording")).toBeInTheDocument();
    });

    it("reverts text on mouse leave", async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<RecordingIndicator state="recording" durationSeconds={60} onToggle={onToggle} />);

      const button = screen.getByRole("button");
      await user.hover(button);
      expect(screen.getByText("Stop Recording")).toBeInTheDocument();

      await user.unhover(button);
      expect(screen.getByText("Recording 01:00")).toBeInTheDocument();
    });

    it("does not change text on hover during transitioning", async () => {
      const user = userEvent.setup();
      const onToggle = vi.fn();
      render(<RecordingIndicator state="starting" onToggle={onToggle} />);

      const button = screen.getByRole("button");
      await user.hover(button);

      // Should still show transitioning text
      expect(screen.getByText("Starting...")).toBeInTheDocument();
    });
  });

  describe("canToggle logic", () => {
    const testCases: {
      state: RecordingState;
      disabled: boolean;
      hasOnToggle: boolean;
      shouldBeDisabled: boolean;
    }[] = [
      { state: "idle", disabled: false, hasOnToggle: true, shouldBeDisabled: false },
      { state: "idle", disabled: true, hasOnToggle: true, shouldBeDisabled: true },
      { state: "starting", disabled: false, hasOnToggle: true, shouldBeDisabled: true },
      { state: "recording", disabled: false, hasOnToggle: true, shouldBeDisabled: false },
      { state: "stopping", disabled: false, hasOnToggle: true, shouldBeDisabled: true },
      { state: "stopped", disabled: false, hasOnToggle: true, shouldBeDisabled: false },
      { state: "error", disabled: false, hasOnToggle: true, shouldBeDisabled: false },
    ];

    for (const { state, disabled, hasOnToggle, shouldBeDisabled } of testCases) {
      it(`button ${shouldBeDisabled ? "disabled" : "enabled"} when state=${state}, disabled=${disabled}`, () => {
        const onToggle = hasOnToggle ? vi.fn() : undefined;
        render(<RecordingIndicator state={state} onToggle={onToggle} disabled={disabled} />);

        if (hasOnToggle) {
          const button = screen.getByRole("button");
          if (shouldBeDisabled) {
            expect(button).toBeDisabled();
          } else {
            expect(button).not.toBeDisabled();
          }
        }
      });
    }
  });
});

describe("useRecordingState", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe("initial state", () => {
    it("starts with idle state", () => {
      const { result } = renderHook(() => useRecordingState());

      expect(result.current.state).toBe("idle");
    });

    it("starts with 0 duration", () => {
      const { result } = renderHook(() => useRecordingState());

      expect(result.current.durationSeconds).toBe(0);
    });
  });

  describe("startRecording", () => {
    it("transitions to starting immediately", () => {
      const { result } = renderHook(() => useRecordingState());

      act(() => {
        result.current.startRecording();
      });

      expect(result.current.state).toBe("starting");
    });

    it("transitions to recording after 1 second", () => {
      const { result } = renderHook(() => useRecordingState());

      act(() => {
        result.current.startRecording();
      });

      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.state).toBe("recording");
    });
  });

  describe("stopRecording", () => {
    it("transitions to stopping immediately", () => {
      const { result } = renderHook(() => useRecordingState());

      // Start recording first
      act(() => {
        result.current.startRecording();
      });
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Now stop
      act(() => {
        result.current.stopRecording();
      });

      expect(result.current.state).toBe("stopping");
    });

    it("transitions to stopped after 1 second", () => {
      const { result } = renderHook(() => useRecordingState());

      // Start and complete recording
      act(() => {
        result.current.startRecording();
      });
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Stop recording
      act(() => {
        result.current.stopRecording();
      });
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.state).toBe("stopped");
    });
  });

  describe("toggleRecording", () => {
    it("starts recording when idle", () => {
      const { result } = renderHook(() => useRecordingState());

      act(() => {
        result.current.toggleRecording();
      });

      expect(result.current.state).toBe("starting");
    });

    it("stops recording when recording", () => {
      const { result } = renderHook(() => useRecordingState());

      // Start recording
      act(() => {
        result.current.startRecording();
      });
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      // Toggle should stop
      act(() => {
        result.current.toggleRecording();
      });

      expect(result.current.state).toBe("stopping");
    });

    it("starts recording when stopped", () => {
      const { result } = renderHook(() => useRecordingState());

      // Complete a recording cycle
      act(() => {
        result.current.startRecording();
      });
      act(() => {
        vi.advanceTimersByTime(1000);
      });
      act(() => {
        result.current.stopRecording();
      });
      act(() => {
        vi.advanceTimersByTime(1000);
      });

      expect(result.current.state).toBe("stopped");

      // Toggle should start again
      act(() => {
        result.current.toggleRecording();
      });

      expect(result.current.state).toBe("starting");
    });

    it("does nothing during transitioning states", () => {
      const { result } = renderHook(() => useRecordingState());

      act(() => {
        result.current.startRecording();
      });

      // While starting, toggle should not change state
      const stateBeforeToggle = result.current.state;
      act(() => {
        result.current.toggleRecording();
      });

      expect(result.current.state).toBe(stateBeforeToggle);
    });
  });
});
