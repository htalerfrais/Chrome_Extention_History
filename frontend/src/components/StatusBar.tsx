interface StatusBarProps {
  status: string;
}

export default function StatusBar({ status }: StatusBarProps) {
  return (
    <div className="bg-black text-white">
      <div className="w-full px-6 py-2 flex items-center justify-between">
        <span className="text-xs text-white/70">{status}</span>
      </div>
    </div>
  );
}
