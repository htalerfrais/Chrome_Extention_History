interface HeaderProps {
  onSettings: () => void;
}

export default function Header({ 
  onSettings
}: HeaderProps) {
  return (
    <header className="bg-black text-white sticky top-0 z-[100]">
      <div className="flex items-center justify-between w-full px-6 py-4">
        <div className="flex items-center gap-3">
          <h1 className="text-sm tracking-widest uppercase">Obra</h1>
        </div>

        <div className="flex items-center gap-3">
          <button className="text-white/70 hover:text-white" onClick={onSettings}>
            Settings
          </button>
        </div>
      </div>
    </header>
  );
}
