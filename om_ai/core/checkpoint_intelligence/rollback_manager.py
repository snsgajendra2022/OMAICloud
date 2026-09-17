class RollbackManager:



    def rollback(
        self,
        checkpoint
    ):


        return {

            "rollback":

                checkpoint.version,

            "status":

                "restored"

        }