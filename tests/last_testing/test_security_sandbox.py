from om_ai.security import SecurityController




security = SecurityController()



def create_file():

    return "file created"




result = security.execute(

    "coding",

    "create file",

    create_file

)



print(result)