from om_ai.observability import OMMonitor



monitor = OMMonitor()



monitor.execution_started(

    "coding_agent"

)


monitor.execution_failed(

    "tool timeout"

)



print(

    monitor.status()

)