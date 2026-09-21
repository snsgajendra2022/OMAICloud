type Props = { active: boolean };

export function MicIndicator({ active }: Props) {
  return (
    <span title={active ? "Listening" : "Mic idle"}>
      <span className={`mic ${active ? "on" : ""}`} /> {active ? "Listening" : "Ready"}
    </span>
  );
}
