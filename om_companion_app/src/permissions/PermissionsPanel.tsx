export function PermissionsPanel() {
  return (
    <section className="panel" style={{ margin: "1rem" }}>
      <h2>Permissions</h2>
      <ul>
        <li>Microphone — required for voice</li>
        <li>Screen capture — optional multimodal</li>
        <li>Files / Terminal / Browser — prompted per capability</li>
      </ul>
    </section>
  );
}
