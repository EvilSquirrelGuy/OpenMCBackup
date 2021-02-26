#! /usr/local/bin/python3.8
#
#    OpenMCBackup - An open source backup utility for minecraft worlds
#    Copyright (C) 2021  EvilSquirrelGuy
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License along
#    with this program; if not, write to the Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#

from rcon.client import Client
import datetime as dt
import tarfile
import shutil
import time
import sys
import os

def logOutput(entry, verboseOverride=False):
  verbose = False
  if '--verbose' in sys.argv:
    verbose = True

  logfile = open('backup.log', 'a')

  if verboseOverride == True or verbose == True:
    print(entry)
  logfile.write('[%s] %s\n' % (dt.datetime.now().strftime('%H:%M:%S.%f')[:-3], entry))


def prepareTempLocation():
  os.system('rm -rf /tmp/openmcbackup')
  os.system('mkdir -p /tmp/openmcbackup/world/region')
  os.system('mkdir -p /tmp/openmcbackup/world/DIM-1/region')
  os.system('mkdir -p /tmp/openmcbackup/world/DIM1/region')
  try:
    os.system('mkdir ../partial')
  except:
    pass
  try:
    os.system('mkdir ../full')
  except:
    pass


def readConfig():
  configOptions = ['defaultBackupType','worldStorageLocation','appName','tempStorage','backupStorage','partialEnabled', 'fullEnabled','additionalFolders','autoSave']
  configDefaultValues = ['partial', '/root/server/world', 'openbackup', '/tmp', '..', 'true', 'false', '', 'true']
  try:
    logOutput('Atttempting to read config file...')
    configFile = open('backup.cfg')
    logOutput('Successfully found config file')

  except FileNotFoundError:
    logOutput('No valid config file found: One will be created')
    configFile = open('backup.cfg', 'x') #create the file
    # Creating default file
    header = '# OpenMCBackup configuration file #\n# Full information on configuration options can be found here:\n# https://openmcbackup.readthedocs.io' #This writes all the stuff for humans to read.
    logOutput('Initialising config file...')
    configFile.write(header)

    for x in range(len(configOptions)):
      configFile.write('%s=%s\n' % (configOptions[x], configDefaultValues[x]))

  finally:
    configFile.close()

  configFile = open('backup.cfg', 'r+').split('\n')
  trimmedConfig = []

  for x in configFile:
    tempStore = ''
    for char in x:
      if char != '#':
        tempStore += char
      else:
        break
    trimmedConfig.append(tempStore)


def purgeOutdated():
  #purge partials older than 48h
  partials = os.listdir('/root/server/backups/partial/')
  for x in partials:
    file = '/root/server/backups/partial/%s' % (x)
    file_time = os.path.getmtime(file) 
      # Check against 24 hours 
    age = (time.time() - file_time) / 3600 > 48 #48 hours
    if age >= 48:
      logOutput('Deleting outdated partial backup %s' % ('/root/server/backups/partial/'+x))
      os.system('rm -f %s' % ('/root/server/backups/partial/'+x))

  fulls = os.listdir('/root/server/backups/full/')
  for x in fulls:
    file = '/root/server/backups/full/%s' % (x)
    file_time = os.path.getmtime(file) 
      # Check against 24 hours 
    age = (time.time() - file_time) / 3600 > 240 #48 hours
    if age >= 240:
      logOutput('Deleting outdated full backup %s'% ('/root/server/backups/full/'+x))
      os.system('rm -f %s' % ('/root/server/backups/full/'+x))
  
  logOutput('Successfully purged all outdated backups')
    

def saveAll():
  with Client('127.0.0.1', 25566, passwd='RCONPasswordHere') as client:
    client.run('save-off')
    client.run('save-all')


def getPartial(worldFolder):
  #OVERWORLD -2k to 2k (root)
  for x in range(-4, 4):
    for z in range(-4, 4):
      filename = 'r.%s.%s.mca' % (x, z)
      logOutput('Copying %s to %s' % (os.path.join(worldFolder,'region',filename), '/tmp/openmcbackup/world/region/'+filename))
      shutil.copy2(os.path.join(worldFolder,'region',filename), '/tmp/openmcbackup/world/region')

  #NETHER -1k to 1k (DIM-1)
  for x in range(-2, 2):
    for z in range(-2,2):
      filename = 'r.%s.%s.mca' % (x, z)
      logOutput('Copying %s to %s' % (os.path.join(worldFolder,'DIM-1','region',filename), '/tmp/openmcbackup/world/DIM-1/region/'+filename))
      shutil.copy2(os.path.join(worldFolder,'DIM-1','region',filename), '/tmp/openmcbackup/world/DIM-1/region')

  #END -512 to 512 (main island) (DIM1)
  for x in range(-1, 1):
    for z in range(-1, 1):
      filename = 'r.%s.%s.mca' % (x, z)
      logOutput('Copying %s to %s' % (os.path.join(worldFolder,'DIM1','region',filename), '/tmp/openmcbackup/world/DIM1/region/'+filename))
      shutil.copy2(os.path.join(worldFolder,'DIM1','region',filename), '/tmp/openmcbackup/world/DIM1/region')


def getFull(worldFolder):
  #Copies EVERYTHING IN REGION FILES (not partial)
  shutil.copytree(os.path.join(worldFolder,'playerdata'), '/tmp/openmcbackup/world/playerdata')
  shutil.copytree(os.path.join(worldFolder,'region'), '/tmp/openmcbackup/world/region') #OVERWORLD (root) 
  shutil.copytree(os.path.join(worldFolder,'DIM-1','region'), '/tmp/openmcbackup/world/region') #NETHER (DIM-1)

  #END (DIM1) Entire dimension is not saved as this wastes storage space and 
  for x in range(-1, 1):
    for z in range(-1, 1):
      filename = 'r.%s.%s.mca' % (x, z)
      logOutput('Copying %s to %s' % (os.path.join(worldFolder,'DIM1','region',filename), '/tmp/openmcbackup/world/DIM1/region/'+filename))
      shutil.copy2(os.path.join(worldFolder,'DIM1','region',filename), '/tmp/openmcbackup/world/DIM1/region')


def makeTarfile(sourceDir, backupType):
  outputFilename = dt.datetime.now().strftime('%Y-%m-%d-%H%M%S')+'.tar.gz....'
  logOutput('Creating archive %s' % outputFilename)
  with tarfile.open('../' + backupType + '/' + outputFilename, "w:gz") as tar:
    tar.add(sourceDir, arcname=os.path.basename(sourceDir))

logOutput('Creating new backup')
prepareTempLocation()
saveAll()

backupType = 'partial'

try:
  if '--partial' in sys.argv:
    backupType = 'partial'
    getPartial('/root/server/world')

  if '--full' in sys.argv:
    backupType = 'full'
    getFull('/root/server/world')

except Exception as e:
  logOutput(e)

start = time.time()

purgeOutdated()
makeTarfile('/tmp/openmcbackup', backupType)

end = time.time()

logOutput('Process completed successfully in %s seconds\n' % (str(round(end-start,2))), True)