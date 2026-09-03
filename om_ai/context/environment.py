"""
OM Environment Awareness
"""

import platform


class EnvironmentDetector:



    def detect(self):


        return {


            "os":

                platform.system(),


            "python":

                platform.python_version(),


            "machine":

                platform.machine()

        }