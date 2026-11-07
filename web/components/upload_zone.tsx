"use client";

type UploadZoneProps = {
  disabled?: boolean;
  readyLabel?: string;
  onFile: (file: File) => void;
  error?: string | null;
};

export function UploadZone({
  disabled,
  readyLabel,
  onFile,
  error,
}: UploadZoneProps) {
  return (
    <label className={`upload ${readyLabel ? "upload--ready" : ""}`}>
      <input
        type="file"
        accept=".pdf,.docx,.txt,application/pdf,text/plain,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        disabled={disabled}
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) onFile(file);
          event.currentTarget.value = "";
        }}
      />
      <span className="upload__eyebrow">Document</span>
      <span className="upload__title">
        {readyLabel ? readyLabel : "Drop a PDF, DOCX, or TXT"}
      </span>
      <span className="upload__hint">Max 4MB. Text PDFs only.</span>
      {error ? <span className="upload__error">{error}</span> : null}
    </label>
  );
}
