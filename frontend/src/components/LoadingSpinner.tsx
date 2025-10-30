// LoadingSpinner component for showing loading state
// This will display a spinner and loading message

export default function LoadingSpinner() {
  return (
    <div className="w-full py-16 flex flex-col items-center justify-center text-white/40 uppercase tracking-[0.35em] text-xs">
      <span>Analyzing Session</span>
    </div>
  );
}
