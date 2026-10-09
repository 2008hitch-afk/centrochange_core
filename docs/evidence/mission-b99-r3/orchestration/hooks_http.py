import lab,types,sys,pathlib,os
os.umask(0o077);lab.isolation()
stub=types.ModuleType('mission97_lab')
for name,value in [('PROJECT',lab.PROJECT),('SITE',lab.SITE),('PORT',lab.PORT),('PRIVATE',lab.ROOT),('ROOT',lab.SOURCE),('isolation',lab.isolation)]:setattr(stub,name,value)
def execute(code):return lab.execute(code.replace('mission97.local',lab.SITE))
stub.execute=execute;sys.modules['mission97_lab']=stub
name=sys.argv[1];assert name in ['mission97_hooks','mission97_http'];script=lab.SOURCE/'infra'/ (name+'.py');sys.argv=[str(script),*sys.argv[2:]]
exec(compile(script.read_text(),str(script),'exec'),{'__name__':'__main__','__file__':str(script)})
