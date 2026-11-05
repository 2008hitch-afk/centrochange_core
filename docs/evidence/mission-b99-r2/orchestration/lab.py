import ops,pathlib,subprocess
ROOT=ops.ROOT;SOURCE=ops.SOURCE;PROJECT=ops.PROJECT;SITE=ops.SITE;PORT=8099;BACKEND=ops.BACKEND;SHA='e85fce588de6012a47da302710b9f9c615211279'
isolation=ops.isolation;redact=ops.redact;execute=ops.execute;compose=ops.compose
def values():return dict(x.split('=',1) for x in (ROOT/'runtime.env').read_text().splitlines())
