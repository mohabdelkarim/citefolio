"use client";

type FeedbackRowProps = {
  disabled?: boolean;
  onRate: (rating: 1 | -1) => void;
  note?: string | null;
};

export function FeedbackRow({ disabled, onRate, note }: FeedbackRowProps) {
  return (
    <div className="feedback">
      <span className="feedback__label">Was this useful?</span>
      <button type="button" disabled={disabled} onClick={() => onRate(1)}>
        Yes
      </button>
      <button type="button" disabled={disabled} onClick={() => onRate(-1)}>
        No
      </button>
      {note ? <span className="feedback__note">{note}</span> : null}
    </div>
  );
}
