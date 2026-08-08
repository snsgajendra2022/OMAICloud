from om_ai.agents import AgentOrchestrator
from om_ai.actions import SafeShellTool

def test_shell_allowlist():
    a=AgentOrchestrator(); t=SafeShellTool(['echo']); a.register_tool(t)
    ok=t.run(command='echo hello'); bad=t.run(command='uname -a')
    assert ok.ok and 'hello' in ok.data['stdout']
    assert not bad.ok
