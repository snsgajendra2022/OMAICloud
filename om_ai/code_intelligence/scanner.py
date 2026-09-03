"""
OM Repository Scanner

Finds files inside a project.
"""


from pathlib import Path




class RepositoryScanner:



    def scan(

        self,

        path:str

    ):


        root = Path(path)


        files=[]



        ignored=[

            ".git",

            "node_modules",

            "__pycache__",

            ".venv",

            "vendor",

            "artifacts",

            "checkpoints",

            "datasets",

            ".cursor",

            ".pytest_cache",

            "dist",

            "build",

        ]

        skip_suffixes = {

            ".pt",
            ".pth",
            ".bin",
            ".onnx",
            ".safetensors",
            ".sqlite3",
            ".sqlite3-shm",
            ".sqlite3-wal",
            ".db",
            ".npz",
            ".jpg",
            ".jpeg",
            ".png",
            ".gif",
            ".webp",
            ".zip",
            ".tar",
            ".gz",
            ".whl",
            ".so",
            ".dylib",
            ".pyc",
        }



        for file in root.rglob("*"):


            if not file.is_file():

                continue



            if any(

                item in file.parts

                for item in ignored

            ):

                continue

            if file.suffix.lower() in skip_suffixes:

                continue

            try:

                if file.stat().st_size > 2_000_000:

                    continue

            except OSError:

                continue



            files.append(

                str(file)

            )


        return files