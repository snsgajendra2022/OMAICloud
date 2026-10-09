from om_ai.security import SecurityController
from om_ai.security.audit_log import AuditLogger



security = SecurityController()



def demo():

    return "created"




result = security.execute(

    agent="coding_agent",

    action="create file",

    resource="file_writer",

    function=demo

)



print(result)



audit = AuditLogger()



logs = audit.query(

    "default",

    limit=10

)



for item in logs:

    print(item.to_dict())