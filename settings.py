# XLS SETTINGS
RI_INPUT_TEMPLATE = True

# PLAN SETTINGS
PLAN_TYPE = 'compute'
TENANCY = ['Shared']
PLAN_LENGTH = [1,3]
PLAN_COMMIT = ['N', 'A']
OSES = ['Linux', 'RHEL', 'RHEL with SQL Ent', 'RHEL with SQL Std', 'RHEL with SQL Web', 'Red Hat Enterprise Linux with HA', 'Red Hat Enterprise Linux with HA with SQL Ent', 'Red Hat Enterprise Linux with HA with SQL Std', 'SUSE', 'Windows', 'Windows with SQL Ent', 'Windows with SQL Std', 'Windows with SQL Web', 'Linux with SQL Ent', 'Linux with SQL Std', 'Linux with SQL Web', 'BYOL']

#如果 PLAN_TYPE 類型為 ec2，則要抓 INSTANCE_FAMILY；compute類型全抓
INSTANCE_FAMILY = ['t3','t3a']                                
