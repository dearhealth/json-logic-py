from projen.python import PythonProject

project = PythonProject(
    author_email="alex.vanloon@dearhealth.com",
    author_name="alexvanloon",
    module_name="json_logic",
    name="dh-json-logic",
    version="0.1.0",
)

project.synth()