type Props = { hudUrl: string; onMic?: (on: boolean) => void };

export function AvatarPanel({ hudUrl, onMic }: Props) {
  return (
    <section className="panel">
      <h2>Presence</h2>
      <iframe className="hud" title="OM HUD" src={hudUrl} allow="microphone" />
      <p>
        <button type="button" onClick={() => onMic?.(true)}>Enable mic (in HUD)</button>
      </p>
    </section>
  );
}
