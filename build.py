import os
import sys
import tarfile
from cStringIO import StringIO

def build(version, source_dir, template, output):
    out = StringIO()
    with tarfile.open(mode='w:gz', fileobj=out) as tar:
        for filename in os.listdir(source_dir):
            full_path = os.path.join(source_dir, filename)
            if os.path.isfile(full_path):
                tar.add(name=full_path, arcname=filename)
    with file(template, "rb") as inf:
        with file(output, "wb") as outf:
            outf.write(inf.read()
                .replace("%%%DATA%%%", out.getvalue().encode("base64"))
                .replace("%%%VERSION%%%", version)
            )

if __name__ == "__main__":
    build(*sys.argv[1:])
