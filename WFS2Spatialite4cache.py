# -*- coding: utf-8 -*-
"""QGIS python layer provider test.

This module is a Python implementation of (a clone of) the core memory
vector layer provider, to be used for test_provider_python.py

.. note:: This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
"""
__author__ = 'Frederic BOURRELLON'
__date__ = '2018-04-05'
__copyright__ = 'Copyright 2018, The QGIS Project'
# This will get replaced with a git SHA1 when you do a git archive
__revision__ = '1.009d'

import os, win32api,time, sys
import urllib.parse
import xml.etree.ElementTree as ET
import datetime
import re
#import urllib.request
#import ssl

"""

# CONVERTIR EN AUTOMATIQIE TT LES COUCHE WFS DU PROJET EN WFS2SQL4C

# EN MANUEL (pour test) modification d'un proj qgs:
ALL FOUNDS: (direct) providerKey="WFS" into providerKey="WFS2SQL4C"
ALL FOUNDS: (direct) <provider encoding="System">WFS2SQL4C</provider> into <provider encoding="System">WFS2SQL4C</provider>
                     <provider encoding="UTF-8">WFS</provider> 
                     *****  ATTENTION ENCODING PROBLEME checher WFS</provider> remplacer par WFS2SQL4C</provider>    *****
ALL FOUNDS: (virtual layers):  providerKey="virtual" with ?layer=WFS2SQL4C:  into  providerKey="virtual" with ?layer=WFS2SQL4C:


WARNING : pageSize='25500' si inférieur au nombre d'elements plantage / WGS pagingn'est pas géré ????
           pagingEnabled='false' OBLIGATOIRE....
"""
from qgis.core import (
    Qgis,
    QgsField,
    QgsFields,
    QgsLayerDefinition,
    QgsPointXY,
    QgsReadWriteContext,
    QgsVectorLayer,
    QgsFeatureRequest,
    QgsFeature,
    QgsGeometry,
    QgsProject,
    QgsWkbTypes,
    QgsExpression,
    QgsExpressionContext,
    QgsExpressionContextUtils,
    QgsCoordinateTransform,
    QgsMemoryProviderUtils,
    QgsCoordinateReferenceSystem,
    QgsRectangle,
    QgsTestUtils,
    QgsVectorDataProvider,
    QgsAbstractFeatureSource,
    QgsAbstractFeatureIterator,
    QgsFeatureIterator,
    QgsApplication,
    QgsProviderRegistry,
    QgsProviderMetadata,
    QgsGeometryEngine,
    QgsSpatialIndex,
    QgsDataProvider,
    QgsCsException,
    QgsVectorFileWriter,
    QgsDataSourceUri,
    QgsMessageLog,
    QgsDataSourceUri,
    QgsNetworkAccessManager,
    QgsSettings,
    NULL
    )
from PyQt5.QtNetwork import  QNetworkRequest
from PyQt5.QtCore import QCoreApplication, QUrl

from qgis.core import QgsLayerTreeLayer
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtCore import QVariant

class PyWfs2Spatia4cacheProvider(QgsVectorDataProvider):

    @classmethod
    def providerKey(self):

        return "WFS2SQL4C" #'Wfs2Spatia4cache'

    @classmethod
    def description(self):
        """Returns the memory provider description"""
        return 'Python Wfs2Spatia4cache Provider'

    @classmethod
    def createProvider(self, uri, providerOptions):
        #QgsMessageLog.logMessage("Message createProvider" , 'WFS2SQL4PROVIDERINIT (LOAD)',level=Qgis.MessageLevel(1) )
        return PyWfs2Spatia4cacheProvider(uri, providerOptions)

    # Implementation of functions from QgsVectorDataProvider
    def cleanupProvider(self):
        self.cachelayer=None
        # NOT USED....
        QgsMessageLog.logMessage("Message cleanupProvider" , 'WFS2SQL4PROVIDERINIT (DELETE)',level=Qgis.MessageLevel(1) )
        super().cleanupProvider()

    def handle_errorlog(self, Message, MessageLevel, LevelOfInformation=0):
       if LevelOfInformation>=self.Level:
            Dummy=""
            if MessageLevel==0: #Info
                Dummy="\xB7\xB7\xB7\xB7\xB7\xB7\xB7\xB7"
            if MessageLevel==1: #Warning
                Dummy="\xB7\xB7" 
            if MessageLevel==2: #Critical
                Dummy="\xB7\xB7" 
            if MessageLevel==3: #Success
                Dummy="\xB7\xB7\xB7" 

            QgsMessageLog.logMessage(Dummy+Message , 'WFS2SQL4CACHE (provider plugin)',level=Qgis.MessageLevel(MessageLevel) )
       return

    def get_param(self, uri):

        # format KEYS=VALUES...
        self.xtype="-1"
        sqlopt=""
        if uri.find(' ')>-1:
          parsinguri=QgsDataSourceUri(uri)

          parsingparams={}
          #for ddd  in dictionnaries:
          #   win32api.MessageBox(0, "LOG WRITINGG"+str(ddd)+"--->"+str(dictionnaries[ddd]), 'QGISXXX', 0x00001000) 
          lastindex=0
          """
          uri=uri.replace("\\'","¤")
          win32api.MessageBox(0, "LOG VALUE [URI]--->["+str(uri)+"]", 'QGISXXX', 0x00001000) 
          index=uri.find('=')
          while index>-1:

               key=uri[lastindex:index].lstrip()
               if lastindex!=0:
                   lastindex=key.rfind(' ')
                   key=key[lastindex+1:len(key)].lstrip()

               if uri[index+1:index+1+1]=="'":
                  indexval=uri.find("'",index+3)
               else:
                  indexval=uri.find(' ',index+1)

               if key.lower()=='XXXXfilterXXX':
                     indexval=len(uri)-1

               if indexval>-1:
                     val=uri[index+1:indexval]
               else:
                     val=""
               # avoir '' in the start and end of the string...
               if val[0:1]=="'":
                   val=val[1:len(val)].replace("¤","'")

               parsingparams[key]=val
               #win32api.MessageBox(0, "LOG VALUE ["+str(key)+"]--->["+str(val)+"]", 'QGISXXX', 0x00001000) 
               #index=uri.find('=',indexval+1)
               lastindex=index
               if indexval>-1:
                   index=uri.find('=',indexval+1)
               else:
                   index=-1

          uri=uri.replace("¤","\\'")

          val=parsinguri.param('filter')
          win32api.MessageBox(0, "LOG VALUE ["+str("0")+"]--->["+str(val)+"]", 'QGISXXX', 0x00001000) 
          """

          self.xtype="KEY/VAL"
          if parsinguri.hasParam('typename'):
            self.WFSlayername=parsinguri.param('typename')
            baseANDtable=self.WFSlayername.split(':')
          else:
            self.WFSlayername="NO_TYPENAME_FOUND:NO_TABLE_NO_TYPENAME"
            baseANDtable="NO_TABLE_NO_TYPENAME"

          if parsinguri.hasParam('filter'):
            self.filter=parsinguri.param('filter')
            self.handle_errorlog("[PROVIDER-MAIN] Found FILTER for WFS data ... filter=[%s]" % self.filter,2,85)
          else:
            self.filter=""
            self.handle_errorlog("[PROVIDER-MAIN] NO FILTER for WFS data ... ",0,85)


          if parsinguri.hasParam('url'):
                url=parsinguri.param('url')
                if url.find('?')!=-1:
                   url=url.replace('?','')
                #getvalue=url[9:].split('/')
                self.geoserver=url #url[0:9]+getvalue[0]+'/'
          else:
                self.geoserver="NO_URL_FOUND_"

          if parsinguri.hasParam('sql'):
            self.handle_errorlog("[PROVIDER-MAIN] Found SQL for WFS data %s... " % ("????"),2,55)
            sql=parsinguri.param('sql')
            getvalue=sql.replace(baseANDtable[0]+":","")
            tmpsql=sql.replace(sql,getvalue)
            getvalueX=tmpsql.split("""WHERE""")
            uri=uri.replace(sql,getvalue)
            if len(getvalueX)<2:
               getvalueX=tmpsql.split("""where""")
               #sqlopt=getvalueX[1]
            if len(getvalueX)>1:
                self.sqlopt=getvalueX[1]
                self.handle_errorlog("[PROVIDER-MAIN] Found SQL for WFS data %s... for [%s] => base=[%s], table=[%s] - serveur=[%s] " % (getvalue,sql,baseANDtable[0],baseANDtable[1],uri),2,55)
          else:
            self.sqlopt=""
            #----self.handle_errorlog("[PROVIDER-MAIN] Not SQL Found for WFS data %s... for [%s] => base=[%s], table=[%s] - serveur=[%s] " % (getvalue,sql,baseANDtable[0],baseANDtable[1],uri),2,55)

          
          """
          getvalue=uri.split("filter='")
          """
        # format URL / HTTPS: old style  
        else:
              uri=uri.replace("&VERSION=2.0.0&","&VERSION=1.1.0&")
              uri=uri.replace("&amp;VERSION=2.0.0&amp;","&amp;VERSION=1.1.0&amp;")
              if uri.find('TYPENAME=')==-1:
                getvalue=uri.split('typename=')
              else:
                getvalue=uri.split('TYPENAME=')
              self.WFSlayername=getvalue[1]
              getvalue=self.WFSlayername.split('&')
              self.WFSlayername=getvalue[0]
              #     getvalue=uri[9:].split('/')
              self.geoserver=uri #uri[0:9]+getvalue[0]+'/'
              self.xtype="HTTPS"

        dbbANDtable=self.WFSlayername.split(':')
        self.database=dbbANDtable[0]
        self.table=dbbANDtable[1]
        self.handle_errorlog("[PROVIDER-MAIN] Found WFS data %s... for [%s] => base=[%s], table=[%s] - serveur=[%s] " % (self.xtype,self.WFSlayername,self.database,self.table,self.geoserver),0,15)

    def create_load_syncTable(self):

        uriSync = QgsDataSourceUri()
        uriSync.setDatabase(self.datalocation+self.databasedirlocation+"/"+self.database+".sqlite")
        schema=""
        #uriSync.setDataSource(schema, 'syncWFS','','','obsid')
        uriSync.setDataSource(schema, 'syncWFS','','')
        self.synclayer = QgsVectorLayer(uriSync.uri(), self.database+"."+self.table+'.sync', 'spatialite')
        #first check create the database...
        # if no layer so the base is new, be aware with this: destroy all sync / force sync...
        if not self.synclayer.isValid(): #@ create this...
           self.handle_errorlog("[PROVIDER-SYNC] create_load_syncTable CREATING DATABASE IN PROGRESS2... ",2,25)
           self.synclayer=QgsVectorLayer('None', self.database+"."+self.table+'.sync', "memory")
           self.synclayer.startEditing()
           res = self.synclayer.dataProvider().addAttributes([QgsField("workspace", QVariant.String), QgsField("layer", QVariant.String) , QgsField("maj", QVariant.String), QgsField("extra1", QVariant.String) , QgsField("extra2", QVariant.String),QgsField("timeCheckNetwork", QVariant.String)])
           self.synclayer.commitChanges()
           options = QgsVectorFileWriter.SaveVectorOptions()
           # this flag crash wriniting is file not exist... only for update so ?
           if os.path.isfile(self.datalocation+self.databasedirlocation+"/"+self.database+'.sqlite') :
                     options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer 
           options.driverName = 'SQLite'
           options.layerName = 'syncWFS'
           options.datasourceOptions = [ "SPATIALITE=YES" , ]
           #---- no geom options.layerOptions = ['GEOMETRY_NAME=geom']
           rc, errmsg = QgsVectorFileWriter.writeAsVectorFormat(self.synclayer, self.datalocation+self.databasedirlocation+"/"+self.database+'.sqlite', options)
           if rc != QgsVectorFileWriter.NoError:
                    #print(tmplayer.name(), _writer)
                    #win32api.MessageBox(0, "mlayer.error WRITINGG", 'QGISXXX', 0x00001000) 
                    self.handle_errorlog("[PROVIDER-SYNC] synclayer.load WRITINGG ERR(returncode=%s)=%s" % (str(rc),errmsg),2,25)
           self.synclayer = None
           self.synclayer = QgsVectorLayer(uriSync.uri(), self.database+"."+self.table+'.sync', 'spatialite')
        else: #@ load this...
           self.handle_errorlog("[PROVIDER-SYNC] create_load_syncTable LOAD DATABASE ... ",3,25)



    def load_maj_syncTable(self):

           uriSync = QgsDataSourceUri()
           uriSync.setDatabase(self.datalocation+self.databasedirlocation+"/"+self.database+".sqlite")
           schema=""
           #uriSync.setDataSource(schema, 'syncWFS','','','obsid')
           #uriSync.setDataSource(schema, 'syncWFS','',""""workspace"='%s' and "layer"='%s'""" % (self.database,self.table))
           uriSync.setDataSource(schema, 'syncWFS','','')
           self.synclayer = QgsVectorLayer(uriSync.uri(), self.database+"."+self.table+'.sync', 'spatialite')
           self.synclayer.dataProvider().forceReload()   # do an refresh of the datasource
           try:
               Filter = QgsExpression("workspace='%s' and layer='%s'" % (self.database,self.table))
               request = QgsFeatureRequest(Filter)
               #request.setSubsetOfAttributes(['idu'], ParcelleLayer.fields())
               request.setLimit(3)
               feats=self.synclayer.getFeatures( request  )
               nExist = int(len(list(feats)))   
           except:
               nExist = 999999
               pass 

           self.synclayer=None
           uriSync.setDataSource(schema, 'syncWFS','','')
           self.synclayer = QgsVectorLayer(uriSync.uri(), self.database+"."+self.table+'.sync', 'spatialite')
           self.synclayer.dataProvider().forceReload()   # do an refresh of the datasource

           #self.synclayer.setSubsetString( "" )
           #self.iface.mapCanvas().refresh()
           #self.synclayer.setSubsetString( """"workspace"='%s' and "layer"='%s'""" % (self.database,self.table) )
           #self.iface.mapCanvas().refresh()
           #--           win32api.MessageBox(0, str(synclayer.featureCount()), 'QGISXXX', 0x00001000) 
           if nExist==0:
                    self.handle_errorlog("[PROVIDER-SYNC] INIT synclayer.VALUE==%s for %s - %s " % ('INIT',self.database,self.table),0,21)
                    fields = self.synclayer.fields()
                    self.synclayer.startEditing()
                    #res = synclayer.dataProvider().addAttributes([QgsField("workspace", QVariant.String), QgsField("layer", QVariant.String) , QgsField("maj", QVariant.String), QgsField("extra1", QVariant.String) , QgsField("extra2", QVariant.String)])
                    featureList = []
                    feature = QgsFeature()
                    # inform the feature of its fields
                    feature.setFields(fields)
                    feature['workspace'] = self.database
                    feature['layer'] = self.table
                    feature['timechecknetwork'] = 0
                    featureList.append(feature)
                    self.synclayer.dataProvider().addFeatures(featureList)
                    self.synclayer.commitChanges()
                    self.synclayer = None
                    self.synclayer = QgsVectorLayer(self.get_local_uri().uri(), self.database+"."+self.table+'.sync', 'spatialite')
                    return "UPDATE_NOW", time.time() 
           else:
                    self.handle_errorlog("[PROVIDER-SYNC] LOAD/MAJ synclayer.VALUE==[%s] for %s - %s " % ('MAJ',self.database,self.table),0,21)
                    if nExist==1:
                        for feature in self.synclayer.getFeatures(request):
                            self.handle_errorlog("[PROVIDER-SYNC] load_maj_syncTable synclayer.VALUE==>%s, time=%s for %s - %s " % (feature['maj'], feature['timechecknetwork'],self.database,self.table),0,21)
                            return feature['maj'], feature['timechecknetwork']

                    else:
                            self.handle_errorlog("[PROVIDER-SYNC] load_maj_syncTable SYNC WFS TABLE: MULTIPLE VALUES IS IMPOSSIBLE...",2,210)
                            return "ERROR_NOW", 0
           return "", 0 

    def update_syncTable(self, CurrentMAJ=None):
            # record MAJ 
           uriSync = QgsDataSourceUri()
           uriSync.setDatabase(self.datalocation+self.databasedirlocation+"/"+self.database+".sqlite")
           schema=""
           #uriSync.setDataSource(schema, 'syncWFS','','','obsid')
           uriSync.setDataSource(schema, 'syncWFS','',""""workspace"='%s' and "layer"='%s'""" % (self.database,self.table))
           self.synclayer = QgsVectorLayer(uriSync.uri(), self.database+"."+self.table+'.sync', 'spatialite')
           nExist=self.synclayer.featureCount()
           if nExist>0:
                 self.synclayer.startEditing()
                 for feature in self.synclayer.getFeatures():
                    self.handle_errorlog("[PROVIDER-LOAD] SET synclayer.VALUE==%s for %s - %s " % (feature['maj'],self.database,self.table),0,34)
                    if CurrentMAJ is not None:
                       feature['maj']=CurrentMAJ
                    feature['timechecknetwork'] = time.time()
                    feature['extra1']="updateDate="+datetime.datetime.now().strftime("%Y/%m/%d a %H:%M:%S")
                    self.synclayer.updateFeature(feature)
                 self.synclayer.commitChanges()
                 if CurrentMAJ is not None:
                      return CurrentMAJ
                 else:
                      return "UPDATE_TIME_NOW"
           else:
                    self.handle_errorlog("[PROVIDER-LOAD] INIT synclayer.VALUE==%s for %s - %s " % ('INIT',self.database,self.table),0,21)
                    fields = self.synclayer.fields()
                    self.synclayer.startEditing()
                    #res = synclayer.dataProvider().addAttributes([QgsField("workspace", QVariant.String), QgsField("layer", QVariant.String) , QgsField("maj", QVariant.String), QgsField("extra1", QVariant.String) , QgsField("extra2", QVariant.String)])
                    featureList = []
                    feature = QgsFeature()
                    # inform the feature of its fields
                    feature.setFields(fields)
                    feature['workspace'] = self.database
                    feature['layer'] = self.table
                    if CurrentMAJ is not None:
                         feature['maj'] = "NEW_NOW"
                    else:
                         feature['maj'] = "UPDATE_TIME_NOW"
                    feature['timechecknetwork'] = time.time()
                    featureList.append(feature)
                    self.synclayer.dataProvider().addFeatures(featureList)
                    self.synclayer.commitChanges()
                    self.synclayer = None
                    self.synclayer = QgsVectorLayer(self.get_local_uri().uri(), self.database+"."+self.table+'.sync', 'spatialite')
                    if CurrentMAJ is not None:
                         return "UPDATE_NOW"

           return "UPDATE_TIME_NOW"

    def get_maj_fromWFSrequest(self, xmlobj, LocalMAJ):
           MAJ="NOMAJ_FOUND" # need to be 4 chars mins !!!!!
           try:
               ET.register_namespace("", "http://www.opengis.net/wfs/2.0")
               ET.register_namespace("", "http://www.opengis.net/wfs/1.0")
               ET.register_namespace("", "http://www.opengis.net/ows/1.1")
               ET.register_namespace("", "ows")
               #-----------------QgsMessageLog.logMessage("xml1====================>[%s]------------------" % str(xmlobj), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
               for xmlsection in xmlobj:
                 #-----------------QgsMessageLog.logMessage("xmlsection2====================>[%s]------------------" % str(xmlsection.tag), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
                 if "FeatureTypeList" in xmlsection.tag:
                     for xmlsubsection in xmlsection:
                            #-----------------QgsMessageLog.logMessage("xmlsubsection3[%s++++++++++]" % str(xmlsubsection.tag), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
                            if "FeatureType" in xmlsubsection.tag:
                                #-----------------QgsMessageLog.logMessage("[xmlsubsection4===============>%s++++++++++]" % str(xmlsubsection.tag), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
                                Keywords=[] #case or the keyword is before the name...
                                bScan=False
                                for attrName in xmlsubsection.iter():
                                      #-----------------QgsMessageLog.logMessage("attrName3----------------------%s %s]" % (attrName.tag,attrName.text), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(2) )
                                      if "keyword" in attrName.tag.lower()  and not "keywords" in attrName.tag.lower():
                                         #-----------------QgsMessageLog.logMessage("attrName4----------------------%s %s]" % (attrName.tag,attrName.text), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(2) )
                                         Keywords.append(attrName.text.lower())
                                      if "Name" in attrName.tag:
                                         #-----------------QgsMessageLog.logMessage("attrName5----------------------%s %s]" % (attrName.text.lower(),self.database+':'+self.table), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(2) )
                                         if attrName.text.lower()==str(self.database+':'+self.table).lower():
                                           #-----------------QgsMessageLog.logMessage("attrName6----------------------%s %s]" % (attrName.tag,attrName.text), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(2) )
                                           bScan=True
                                if bScan:
                                      #-----------------QgsMessageLog.logMessage("KEYWORD==attrKeyNam8=>[++++++++++]", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
                                      for keyword in Keywords:
                                         #-----------------QgsMessageLog.logMessage("KEYWORD==[%s++++++++++%s]" % ( keyword, LocalMAJ ), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
                                         if LocalMAJ.lower()!=keyword and keyword[0:4]=="maj_":
                                            #win32api.MessageBox(0, str( MAJ ), 'title')
                                            self.handle_errorlog("[PROVIDER-SYNC] comparing maj =>%s(local) <??> %s'distant)]" % (LocalMAJ , keyword ),0,21)
                                            MAJ=keyword
                                            self.bUpdate=True
                                            return MAJ
                                         if LocalMAJ.lower()==keyword and keyword[0:4]=="maj_":
                                            self.bUpdate=False
                                            return "ALREADY_DONE"
           except:
               MAJ="ERROR"
               pass
           return MAJ

    def get_local_uri(self):

        uriLoad = QgsDataSourceUri()
        uriLoad.setDatabase(self.datalocation+self.databasedirlocation+"/"+self.database+".sqlite")
        schema = ''
        #geom_column = 'Geometry'
        if self.NoGeom:
            geom_column = ''
        else:
            geom_column = 'geom'
        uriLoad.setDataSource(schema, self.table, geom_column, self.sqlopt)
        return uriLoad

    def get_local_layer(self):

        uriLoad = QgsDataSourceUri()
        uriLoad.setDatabase(self.datalocation+self.databasedirlocation+"/"+self.database+".sqlite")
        schema = ''
        #geom_column = 'Geometry'
        if self.NoGeom:
            geom_column = ''
        else:
            geom_column = 'geom'
        uriLoad.setDataSource(schema, self.table, geom_column, self.sqlopt)

        tmp = QgsVectorLayer( uriLoad.uri(), self.database+"."+self.table, 'spatialite')
        self.handle_errorlog("[PROVIDER-LOCAL-LAYER] CREATE ACCESS TO spatialite LOCAL LAYER[%s]: %s" % (str(tmp),self.datalocation+self.databasedirlocation+"/"+self.database+".XXX.sqlite"  ),3,21)
        return tmp 

    def copy_wfs2local_layer(self, uri):


              if self.xtype=="HTTPS": # old style found request command... HTTPS / URL Command...
                 index=uri.lower().find("cql_filter=") # no filter when loading cache...
                 if index!=-1:
                     getRequest=uri[  index:index+len("cql_filter=") ] 
                     if getRequest!="":
                            uri=uri.replace(getRequest,'DESACTIVED_'+getRequest)

                 index=uri.lower().find("filter=") # no filter when loading cache...
                 if index!=-1:
                     getRequest=uri[  index:index+len("filter=") ] 
                     if getRequest!="":
                            uri=uri.replace(getRequest,'DESACTIVED_'+getRequest)


              if self.sqlopt!="":
                 uriLoad = QgsDataSourceUri(uri)
                 uriLoad.setSql("")
                 tmplayer = QgsVectorLayer(uriLoad.uri(True), 'mlWFS', 'WFS')
              else:
                 tmplayer = QgsVectorLayer(uri, 'mlWFS', 'WFS')

              #tmplayer = QgsVectorLayer(uri.replace('sql=','sqloptional='), 'mlWFS', 'WFS')
              if tmplayer.isValid():
                #win32api.MessageBox(0, "mlayer.error WFS OK", 'QGISXXX', 0x00001000) 
                #WKBNoGeometry = 100

                self.handle_errorlog("[PROVIDER-LOAD] Loading WFS data return... %s [%s]" % (os.path.join("???????????"+os.path.dirname(__file__), '/'+self.database+'.XXX.sqlite'), str(tmplayer.wkbType())),0,35)
                # OK----------QgsVectorFileWriter.writeAsVectorFormat(tmplayer, "R:/SU/SIG/PROJET/2019/04-ab-OptimisationWFS-QGIS/temp2.shp", "utf-8", tmplayer.crs(),driverName="ESRI Shapefile")
                options = QgsVectorFileWriter.SaveVectorOptions()
                # this flag crash wriniting is file not exist... only for update so ?
                if os.path.isfile(self.datalocation+self.databasedirlocation+"/"+self.database+'.sqlite') :
                     options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer 
                options.driverName = 'SQLite'
                options.layerName = self.table
                if tmplayer.wkbType()== QgsWkbTypes.NoGeometry:
                    #options.datasourceOptions = [ "SPATIALITE=YES" , ]
                    #options.datasourceOptions = ['SPATIALITE=YES','OGR_SQLITE_PRAGMA=synchronous=OFF,journal_mode=MEMORY,locking_mode=EXCLUSIVE']
                    self.NoGeom=True
                    xpLayer= self.get_local_layer()
                    if xpLayer.dataProvider().wkbType()== QgsWkbTypes.NoGeometry:
                        self.handle_errorlog("[PROVIDER-LOAD] Loading WFS with no GEOM and EXISTING FORCE DELETE... {%s} [%s]" % (str(xpLayer.dataProvider().wkbType()), str(self.table)),2,31)
                        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer + QgsVectorFileWriter.CanDeleteLayer

                    options.datasourceOptions = ['SPATIALITE=YES','SQLITE_LIST_ALL_TABLES=YES','OGR_SQLITE_PRAGMA=SQLITE_LIST_ALL_TABLES=YES']
                    #options.layerOptions = ['SPATIAL_INDEX=NO', 'FID=id','FORMAT=SPATIALITE','GEOMETRY_NAME=geom']
                    #options.layerOptions = ['SPATIAL_INDEX=NO','FORMAT=SPATIALITE']
                    options.layerOptions = ['GEOMETRY_NAME=']
                else:
                    #----options.datasourceOptions = [ "SPATIALITE=YES" , ]
                    self.NoGeom=False
                    options.datasourceOptions = ['SPATIALITE=YES','SQLITE_LIST_ALL_TABLES=YES','OGR_SQLITE_PRAGMA=SQLITE_LIST_ALL_TABLES=YES']
                    #options.datasourceOptions = ['SPATIALITE=YES','OGR_SQLITE_PRAGMA=synchronous=OFF,journal_mode=MEMORY,locking_mode=EXCLUSIVE']
                    options.layerOptions = ['GEOMETRY_NAME=geom']
                    #if self.sqlopt!="":
                    #    self.handle_errorlog("[PROVIDER-LOAD] Loading WFS with  GEOM and EXISTING SQL FILTER APPEND NOT CLEAR AND SAVE... {%s} [%s]" % (str(self.sqlopt), str(self.table)),3,31)
                    #    #options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer + QgsVectorFileWriter.CanAppendToExistingLayer

                """
                win32api.MessageBox(0, "mlayer.error 2WRITINGG", 'QGISXXX', 0x00001000) 
                feats = [feat for feat in tmplayer.getFeatures()]
                win32api.MessageBox(0, "mlayer.error 3WRITINGG", 'QGISXXX', 0x00001000) 
                mem_layer = QgsVectorLayer("Point?crs=epsg:4326", "duplicated_layer", "memory")
                mem_layer_data = mem_layer.dataProvider()
                attr = tmplayer.dataProvider().fields().toList()
                mem_layer_data.addAttributes(attr)
                mem_layer.updateFields()
                mem_layer_data.addFeatures(feats)
                rc, errmsg = QgsVectorFileWriter.writeAsVectorFormat(mem_layer, self.datalocation+self.databasedirlocation+"/"+self.database+'.sqlite', options)
                """
                rc, errmsg = QgsVectorFileWriter.writeAsVectorFormat(tmplayer, self.datalocation+self.databasedirlocation+"/"+self.database+'.sqlite', options)
                if rc != QgsVectorFileWriter.NoError:
                    #print(tmplayer.name(), _writer)
                    #win32api.MessageBox(0, "mlayer.error WRITINGG", 'QGISXXX', 0x00001000) 
                    self.handle_errorlog("[PROVIDER-LOAD] mlayer.error WRITINGG ERR(returncode=%s)=%s" % (str(rc),errmsg),2,360)
                    return True #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                else:
                    self.handle_errorlog("[PROVIDER-LOAD] mlayer WRITING  OK...",0,36)
                    #win32api.MessageBox(0, "mlayer.error NOT WRITINGG", 'QGISXXX', 0x00001000) 
                tmplayer=None
                return True
              else:
                self.handle_errorlog("[PROVIDER-LOAD] mlayer.error WRITINGG ERR VALID(returncode=%s)=%s" % (str(rc),errmsg),2,360)
                return False

    """
                        self.synclayer = QgsVectorLayer(self.get_local_uri().uri(), self.database+"."+self.table+'.sync', 'spatialite')
    """

    def __init__(self, uri='', providerOptions=QgsDataProvider.ProviderOptions()):

        bLoading=False
        bForceLoading=False
        bDisconnected=False
        # 0 = detailled / 1024 = silent / 1000 only  result....

        s = QgsSettings()
        if str(s.value("Wfs2Spatia4cache/forceloading", "EMPTY"))=="RUN":
           bForceLoading=True
        if str(s.value("Wfs2Spatia4cache/loading", "EMPTY"))=="RUN":
           bLoading=True
           bForceLoading=False
        ModeRunning=str(s.value("Wfs2Spatia4cache/mode", "EMPTY"))
        if ModeRunning=="OFF":
           bDisconnected=True

        self.Level=99999
        if str(s.value("Wfs2Spatia4cache/debug", "EMPTY"))!="EMPTY":
           self.Level=int( s.value("Wfs2Spatia4cache/debug", "0")  )

        self.AutoModeWaitInSec=3600
        if str(s.value("Wfs2Spatia4cache/automodewait", "EMPTY"))!="EMPTY":
           self.AutoModeWaitInSec=int( s.value("Wfs2Spatia4cache/automodewait", "3600")  )
          
        self.cachelayer=None
        self.synclayer=None
        #self.Level=1000999
        self.bUpdate=False
        self.xtype="-1"
        self.WFSlayername=""
        self.geoserver=""
        self.database=""
        self.table=""
        self.sqlopt=""
        # geom by default...
        self.NoGeom=False
        self.originalURI=uri
        self.filter=""

        self.handle_errorlog( "[PROVIDER-MAIN] Loading WFS data... for >>>>>%s" % (uri),0,15)
        #* get parameters from uri configuration...
        self.get_param(uri)
        #* to upgrade checck where (username/login dependent and acces rigth)
        self.datalocation=os.getenv('APPDATA')
        self.databasedirlocation="/QGIS-WFS2SQL4C"
        # create directory cache...
        if not os.path.exists(self.datalocation+self.databasedirlocation) :
           os.mkdir(self.datalocation+self.databasedirlocation)

        super().__init__(self.get_local_uri().uri())
        if not bForceLoading and not bLoading:
           self.handle_errorlog("[PROVIDER-INIT] -------------synclayer IS **NOT** IN LOADING STATE !!!!!!!!" ,1,23)
           #* get cache WFS layer...
           #mlayer=self.get_local_layer()
           #if mlayer.isValid():
           bDisconnected=True
           #else:
           #             self.handle_errorlog("[PROVIDER-INIT] -------------synclayer IS **NOT** IN LOADING STATE AND NOT   VALID !!!!!!!!" ,1,23)
        else:
            self.handle_errorlog("[PROVIDER-INIT] +++++++++++++synclayer IS IN LOADING STATE !!!!!!!!" ,1,23)

            #* create sync table to cache and update if required...
            self.create_load_syncTable()
            if self.synclayer==None:
                  self.handle_errorlog("[PROVIDER-SYNC] synclayer IS EMPTY/NULL " ,2,23)
                  return None
            #* get cache WFS layer...
            mlayer=self.get_local_layer()
            if not mlayer.isValid():
                self.NoGeom=True
                mlayer=self.get_local_layer()
                if not mlayer.wkbType()== QgsWkbTypes.NoGeometry:
                    self.NoGeom=False
            # check cache... if exist... compare versions...
            MAJ="NEW_ONE"
            if mlayer.isValid():
               #* found the local(sqlite) MAJ version...
               self.handle_errorlog( "[PROVIDER-SYNC] !!! local base is valid... --------------------------" ,2,164)
               MAJX=self.load_maj_syncTable()
               self.handle_errorlog( "[PROVIDER-SYNC] !!! load_maj_syncTable... %s" % str(MAJX),0,164)
               MAJ=MAJX[0]
               try:
                  MAJTIME=float(MAJX[1])
               except:
                  MAJTIME=time.time()

               if ModeRunning=="AUTO":
                      diffsec = round(time.time()-round(MAJTIME))
                      if diffsec>0 and diffsec<self.AutoModeWaitInSec+30:
                            d=datetime.datetime(1,1,1)+datetime.timedelta(seconds=diffsec)
                            self.handle_errorlog( "[PROVIDER-SYNC] !!! Mode Running AUTO... cache mode is activated... %s seconds as day=%d hour=%d minute=%d second=%d " % (str(diffsec), d.day-1, d.hour, d.minute, d.second),0,164)
                      #      self.handle_errorlog( "[PROVIDER-SYNC] !!! Mode Running AUTO... cache mode is activated..." ,0,164)
                            bDisconnected=True

               if not bDisconnected:   # force no update from server... (disconnected mode)
                   #* found the distant(WFS) MAJ version...
                   self.handle_errorlog( "[PROVIDER-NETWORK] Call NETWORK WFS ... for %s" % (uri),0,65)
                   # SPECIIAL GEOSERVER url = QUrl(self.geoserver+''+self.database+'/'+self.table+'/wfs?SERVICE=WFS&REQUEST=GetCapabilities')
                   if self.xtype=="HTTPS": # old style found request command... HTTPS / URL Command...
                        url = self.geoserver
                        index=url.lower().find("request=")
                        getRequest="NOT_FOUND"
                        if index!=-1:
                              tmp=url.lower().split("request=")
                              index2=tmp[1].find("&")
                              if index2>-1:
                                 getRequest=url[  index:index+len("request=")+index2 ] 
                              else:
                                 getRequest=url[  index:65535 ]
                              if getRequest!="":
                                   url=url.replace(getRequest,'REQUEST=GetCapabilities')
                        else:
                           if url.find("&")==-1:
                               url = self.geoserver+'?REQUEST=GetCapabilities'
                           else:
                               url = self.geoserver+'&REQUEST=GetCapabilities'
                        url2 = url
                        url = QUrl(url)
                        self.handle_errorlog( "[PROVIDER-NETWORK] HTTPS NETWORK WFS ADAPT... for %s , getRequest=[%s]" % (url2,getRequest),0,65)
                   else:   # URI MODE...
                        url = QUrl(self.geoserver+'?SERVICE=WFS&REQUEST=GetCapabilities')
                        self.handle_errorlog( "[PROVIDER-NETWORK] URI NETWORK WFS ... for %s" % (uri),0,65)
                   #        --- take the distant MAJ as  https://MY GEOSERVER/geoserver/WORKSPACE/LAYER/wfs?SERVICE=WFS&REQUEST=GetCapabilities
                   #        (TODO of not geoserver: le global AUSSI FONCTIONNE (moins rapide) car il cherche en xml le WORKSPACE/LAYER: 
                   #----url = QUrl("https://MY GEOSERVER/geoserver/wfs/wfs?request=GetCapabilities")
                   request = QNetworkRequest(url)
                   reply = QgsNetworkAccessManager.instance().get(request)
                   while not reply.isFinished():
                     time.sleep(0.150)
                     # This line is going to update (process) everything which might wait in cue like refreshing
                     QCoreApplication.processEvents()
                   #---------------------------------self.get_maj_fromWFSrequest()
                   #self.handle_errorlog( "[PROVIDER-NETWORK] Call XML RESPONSE NETWORK WFS ... for maj=%s[%s]" % (MAJ,xmlcontent),0,66)
                   self.handle_errorlog( "[PROVIDER-NETWORK] Call XML RESPONSE NETWORK WFS ... for maj=%s[%s]" % (MAJ,url),0,66)
                   MAJ=self.get_maj_fromWFSrequest(ET.fromstring(reply.readAll()),MAJ)
                   if MAJ=="ERROR":
                     self.handle_errorlog( "[PROVIDER-NETWORK] maj VERSION EMPTY..." ,0,64)
                     return None
                   else:
                     self.handle_errorlog( "[PROVIDER-NETWORK] Distant maj=[%s]" % (MAJ),0,64)
            else:
                     self.handle_errorlog( "[PROVIDER-NETWORK] Erreur CHARGEMENT couche en cache ... %s" % (MAJ),0,64)
                     self.bUpdate=True
            """ debug loading no geom table 
            if mlayer.wkbType()== QgsWkbTypes.NoGeometry:
                    self.bUpdate=True
                    MAJ="NEW_ONE"
            """   
            if (MAJ == "NEW_ONE" or MAJ[0:4]=="maj_") and (self.bUpdate and not bDisconnected):
                  self.handle_errorlog("[PROVIDER-LOAD] NEW ONE DETECTED CHECK SYNC...",0,36)
                  #* need to load from WFS network server.... long time...
                  bRes=self.copy_wfs2local_layer(uri)
                  if bRes:
                    #* refresh/reload cache WFS layer...
                    mlayer=self.get_local_layer()
                    if not mlayer.isValid():
                          self.handle_errorlog("[PROVIDER-LOAD] mlayer.error NOT VALID...",2,360)
                          return None
                    else:
                          self.handle_errorlog("[PROVIDER-LOAD] mlayer IS VALID LAYER...",0,36)

                    #* need to save the new MAJ version in local sqlite...
                    if MAJ[0:4]=="maj_" or 1==1: # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
                        if self.update_syncTable(MAJ)=="NO ERROR DETECTED HERE":
                             self.handle_errorlog("[PROVIDER-LOAD] synclayer ne peut etre mise a jour EERREUR " % (feature['maj'],self.database,self.table),2,340)
                             return None
                  else:
                    self.handle_errorlog("[PROVIDER-LOAD] mlayer WFS IS NOT VALID " ,2,330)
                    return None

            if not bDisconnected:
                  self.handle_errorlog("[PROVIDER-LOAD] synclayer  mise a jour TIME SYNC ALL" ,2,440)
                  self.update_syncTable() # update time network checking...
            #if self.update_syncTable(MAJ)==None:
            #                 self.handle_errorlog("[PROVIDER-LOAD] synclayer ne peut etre mise a jour ERREUR SYNC ALL" % (feature['maj'],self.database,self.table),2,340)

            if mlayer!=None:
                  self.cachelayer=mlayer
            else:
                  self.handle_errorlog("[PROVIDER-MAIN] mlayer WFS IS NOT VALID " ,2,299)
                  return None

            if self.filter!="":
                  self.cachelayer.setSubsetString(self.filter)

            #self.setNativeTypes(mlayer.dataProvider().nativeTypes())
            #self._fields = mlayer.fields()
            #self._wkbType = mlayer.wkbType()
            #self._extent = QgsRectangle()
            #self._extent.setMinimal()
            #self._subset_string = ''
            #self._crs = mlayer.crs()
            #self._spatialindex = None
            #self._provider_options = providerOptions
            #if 'index=yes'in self._uri:
            #    self.createSpatialIndex()

            # mlayer.getFeatures()
            #print( mlayer.getFeatures() )
            #self.addAttributes(mlayer.fields())
            #self.addFeatures(mlayer.getFeatures())
            #self.addFeatures(mlayer.getFeatures().attributes())

            if MAJ=="NOMAJ_FOUND": 
                  self.handle_errorlog("[PROVIDER-MAIN] **************** WFS Layer is loaded and cached successfully! (no update system)" ,3,1004)
            if MAJ=="ALREADY_DONE": 
                  self.handle_errorlog("[PROVIDER-MAIN] **************** WFS Layer is loaded from cache successfully! (updated system found and up-to-date)" ,3,1004)
            if MAJ[0:4]=="maj_" and self.bUpdate: 
                  self.handle_errorlog("[PROVIDER-MAIN] **************** WFS Layer is loaded from network and from the cache successfully! (update system found)" ,3,1004)
            if not (MAJ[0:4]=="maj_" and self.bUpdate) and not MAJ=="NOMAJ_FOUND" and not MAJ=="ALREADY_DONE": 
                 self.handle_errorlog("[PROVIDER-MAIN] **************** WFS Layer ending successfully! (no action!)" ,3,1004)

    def featureSource(self):
        #return PyFeatureSource(self)
        #QgsMessageLog.logMessage("mlayer.featureSource ==[%s] " % str(self.cachelayer.dataProvider().featureSource()), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        #return self.cachelayer.dataProvider().featureSource()
        return self.cachelayer.dataProvider().featureSource()

    def handlePostCloneOperations(self, source):
         #self.cachelayer._features = source._features
        # REQUIERED 3.8 not LTR... QgsMessageLog.logMessage("mlayer.handlePostCloneOperations ==[%s] " % str(source), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(2) )
        return 
    

    def dataSourceUri(self, expandAuthConfig=True):
        #----QgsMessageLog.logMessage("mlayer.dataSourceUri ==[%s] " % self.cachelayer.dataProvider().uri(), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(3) )
        #return QgsDataSourceUri(self.originalURI) #self.cachelayer.dataProvider().uri()    QgsDataSourceUri
        #win32api.MessageBox(0, "mlayer WRITINGG"+str(sys._getframe(1).f_globals.get(            '__name__', '__main__')), 'QGISXXX', 0x00001000) 
        
        # POUR PLUGIN CADASTRE: URI DE LA BASE SPATIALIIIIIIITE !!!!!!!! car on fait des appels direct dans la base... sys._getframe().f_back.f_code.co_name
        module=""
        try:
           module= str(sys._getframe(1).f_globals.get('__name__', '__main__') )
        except:
           module="EXCEPT1..."
           pass
           try:
               f = list(sys._current_frames().values())[0]
               module=f.f_back.f_globals['__name__']
           except:
               module="EXCEPT2..."
           pass

        if "cadastre." in module.lower():
            if self.cachelayer==None:
                self.cachelayer=self.get_local_layer()
            return self.cachelayer.dataProvider().uri().uri() #sql obligatoire pour filtrer
            #self.get_local_uri().uri()
        else:
            if self.filter!="": # filter set, not existing...
                if self.xtype=="KEY/VAL":
                       parsinguri=QgsDataSourceUri(self.originalURI)
                       parsinguri.removeParam('filter')
                       if self.filter!="[ERASE]":
                           parsinguri.setParam('filter', self.filter)
                       else:
                           self.filter=""
                       self.originalURI=parsinguri.uri(True)
                else:
                       win32api.MessageBox(0, "mlayer dataSourceUri filter on thhs string NOT POSSIBLE: Filter not saved ---- !!!!!!!!", 'QGISXXX', 0x00001000) 
                       return self.originalURI
            #if self.cachelayer.subsetString()!="":
            #       return self.originalURI+""" filter='"""+self.cachelayer.subsetString()+"""' """
            return self.originalURI

    def storageType(self):
        return "Python WFS To Spatialite For caching storage"

    def dataComment(self):
            #win32api.MessageBox(0, "mlayer WRITINGG", 'QGISXXX___OK', 0x00001000) 
            if self.cachelayer==None:
                self.cachelayer=self.get_local_layer()
            return self.cachelayer.dataProvider().uri().uri() #sql obligatoire pour filtrer


    def getFeatures(self, request=QgsFeatureRequest()):
        #return QgsFeatureIterator(PyFeatureIterator(PyFeatureSource(self), request))
        #return self.cachelayer.dataProvider().featureSource(request))
        # debuging ok QgsMessageLog.logMessage("mlayer.getFeatures ==[%s] " % str(request ), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        #QgsMessageLog.logMessage("mlayer.getFeatures ==[%s] " % str(request.OrderBy.dump()), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        if self.cachelayer==None:
                self.cachelayer=self.get_local_layer()

        return self.cachelayer.getFeatures(request)


    def uniqueValues(self, fieldIndex, limit=1):
        # debuging ok         QgsMessageLog.logMessage("mlayer.uniqueValues index=%s" % ( str(fieldIndex) ), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        if self.cachelayer==None:
                self.cachelayer=self.get_local_layer()
        results = set()
        if fieldIndex >= 0 and fieldIndex < self.cachelayer.fields().count():
            req = QgsFeatureRequest()
            req.setFlags(QgsFeatureRequest.NoGeometry)
            req.setSubsetOfAttributes([fieldIndex])
            for f in self.cachelayer.getFeatures(req):
                results.add(f.attributes()[fieldIndex])
        return results

    def wkbType(self):
        return self.cachelayer.wkbType()

    def featureCount(self):
        return self.cachelayer.featureCount()

    def fields(self):
        return self.cachelayer.fields()

    def addFeatures(self, flist, flags=None):
        #QgsMessageLog.logMessage("mlayer.addFeatures", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        added = False
        f_added = []
        """
        for f in flist:
            if f.hasGeometry() and (f.geometry().wkbType() != self.wkbType()):
                print("PB INSERT FEATURES")
                return added, f_added

        for f in flist:
            _f = QgsFeature(self.fields())
            _f.setGeometry(f.geometry())
            attrs = [None for i in range(_f.fields().count())]
            for i in range(min(len(attrs), len(f.attributes()))):
                attrs[i] = f.attributes()[i]
            _f.setAttributes(attrs)
            _f.setId(self.next_feature_id)
            self._features[self.next_feature_id] = _f
            self.next_feature_id += 1
            added = True
            f_added.append(_f)

            if self._spatialindex is not None:
                self._spatialindex.insertFeature(_f)

        if len(f_added):
            self.clearMinMaxCache()
            self.updateExtents()
        """
        return added, f_added

    def deleteFeatures(self, ids):
        #QgsMessageLog.logMessage("mlayer.deleteFeatures", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        return False
        """
        if not ids:
            return True
        removed = False
        for id in ids:
            if id in self._features:
                if self._spatialindex is not None:
                    self._spatialindex.deleteFeature(self._features[id])
                del self._features[id]
                removed = True
        if removed:
            self.clearMinMaxCache()
            self.updateExtents()
        return removed
        """

    def addAttributes(self, attrs):
        #QgsMessageLog.logMessage("mlayer.addAttributes", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        """
        try:
            for new_f in attrs:
                if new_f.type() not in (QVariant.Int, QVariant.Double, QVariant.String, QVariant.Date, QVariant.Time, QVariant.DateTime, QVariant.LongLong, QVariant.StringList, QVariant.List):
                    continue
                self._fields.append(new_f)
                for f in self._features.values():
                    old_attrs = f.attributes()
                    old_attrs.append(None)
                    f.setAttributes(old_attrs)
            self.clearMinMaxCache()
            return True
        except Exception:
            return False
        """
        return False

    def renameAttributes(self, renamedAttributes):
        #QgsMessageLog.logMessage("mlayer.renameAttributes", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        result = False
        """
        result = True
        # We need to replace all fields because python bindings return a copy from [] and at()
        new_fields = [self._fields.at(i) for i in range(self._fields.count())]
        for fieldIndex, new_name in renamedAttributes.items():
            if fieldIndex < 0 or fieldIndex >= self._fields.count():
                result = False
                continue
            if self._fields.indexFromName(new_name) >= 0:
                #field name already in use
                result = False
                continue
            new_fields[fieldIndex].setName(new_name)
        if result:
            self._fields = QgsFields()
            for i in range(len(new_fields)):
                self._fields.append(new_fields[i])
        """
        return result

    def deleteAttributes(self, attributes):
        #QgsMessageLog.logMessage("mlayer.deleteAttributes", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        return False
        """
        attrIdx = sorted(attributes, reverse=True)

        # delete attributes one-by-one with decreasing index
        for idx in attrIdx:
            self._fields.remove(idx)
            for f in self._features.values():
                attr = f.attributes()
                del(attr[idx])
                f.setAttributes(attr)
        self.clearMinMaxCache()
        return True
        """

    def changeAttributeValues(self, attr_map):
        #QgsMessageLog.logMessage("mlayer.changeAttributeValues", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        return False
        """
        for feature_id, attrs in attr_map.items():
            try:
                f = self._features[feature_id]
            except KeyError:
                continue
            for k, v in attrs.items():
                f.setAttribute(k, v)
        self.clearMinMaxCache()
        return True
        """

    def changeGeometryValues(self, geometry_map):
        #QgsMessageLog.logMessage("mlayer.changeGeometryValues", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        """
        for feature_id, geometry in geometry_map.items():
            try:
                f = self._features[feature_id]
                f.setGeometry(geometry)
            except KeyError:
                continue
        self.updateExtents()
        return True
        """

    def allFeatureIds(self):
        QgsMessageLog.logMessage("mlayer.allFeatureIds", 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        #return list(self._features.keys())
        return list()

    def subsetString(self):
        #---        QgsMessageLog.logMessage("mlayer.SubsetString2 ==[%s] " % self.cachelayer.subsetString(), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        if self.filter!=self.cachelayer.subsetString:
              self.cachelayer.setSubsetString(self.filter)
        return self.cachelayer.subsetString()

    def setSubsetString(self, subsetString, optional=""):
        #---        QgsMessageLog.logMessage("mlayer.setSubsetString VALID ==[%s] -%s" % (subsetString,str(optional)), 'PROV_WFS2SQL4CACHE',level=Qgis.MessageLevel(0) )
        #win32api.MessageBox(0, "mlayer WRITINGG  module="+str(str(optional))+"  uri=<<<"+subsetString+">>>", 'QGISXXX', 0x00001000) 
        if subsetString=="" and self.filter!="":
              self.filter="[ERASE]"
        else:
              self.filter=subsetString
             
        return self.cachelayer.setSubsetString(subsetString)
        """
        if subsetString == self._subset_string:
            return True
        self._subset_string = subsetString
        self.updateExtents()
        self.clearMinMaxCache()
        self.dataChanged.emit()
        return True
        """

    def supportsSubsetString(self):
        return True

    def createSpatialIndex(self):
        """  
        if self._spatialindex is None:
            self._spatialindex = QgsSpatialIndex()
            for f in self._features.values():
                self._spatialindex.insertFeature(f)
        """  
        return True

    def capabilities(self):
        #return QgsVectorDataProvider.AddFeatures | QgsVectorDataProvider.DeleteFeatures | QgsVectorDataProvider.CreateSpatialIndex | QgsVectorDataProvider.ChangeGeometries | QgsVectorDataProvider.ChangeAttributeValues | QgsVectorDataProvider.AddAttributes | QgsVectorDataProvider.DeleteAttributes | QgsVectorDataProvider.RenameAttributes | QgsVectorDataProvider.SelectAtId | QgsVectorDataProvider. CircularGeometries
        return QgsVectorDataProvider.NoCapabilities

    #/* Implementation of functions from QgsDataProvider */
    def name(self):
        return self.providerKey()

    def extent(self):
        return(self.cachelayer.extent())
        """
        if self._extent.isEmpty() and self._features:
            self._extent.setMinimal()
            if not self._subset_string:
                # fast way - iterate through all features
                for feat in self._features.values():
                    if feat.hasGeometry():
                        self._extent.combineExtentWith(feat.geometry().boundingBox())
            else:
                for f in self.getFeatures(QgsFeatureRequest().setSubsetOfAttributes([])):
                    if f.hasGeometry():
                        self._extent.combineExtentWith(f.geometry().boundingBox())

        elif not self._features:
            self._extent.setMinimal()
        return QgsRectangle(self._extent)
        """

    def updateExtents(self):
        #if self.cachelayer.extent.setMinimal()
        #self.cachelayer.extent.setMinimal()
        return

    def isValid(self):
        if self.cachelayer==None:
            self.cachelayer=self.get_local_layer()
        return self.cachelayer.isValid()

    def crs(self):
        return self.cachelayer.crs()


# class for plugin stuff
class PyWfs2Spatia4cacheINIT:

    """QGIS Plugin Implementation."""

	
    def __init__(self, iface):
        """Constructor."""
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        QgsProject.instance().readProject.connect(self.readSession)
        QgsProject.instance().cleared.connect(self.clearSession)

    def readSession(self, doc):
        #QgsMessageLog.logMessage("Message (End) readSession" , 'WFS2SQL4PLUGINIT (LOAD)',level=Qgis.MessageLevel(1) )
        s = QgsSettings()
        s.setValue("Wfs2Spatia4cache/loading", "STOP")
        s.sync()

    def clearSession(self):
        #QgsMessageLog.logMessage("Message (Start) clearSession" , 'WFS2SQL4PLUGINIT (LOAD)',level=Qgis.MessageLevel(1) )
        s = QgsSettings()
        s.setValue("Wfs2Spatia4cache/loading", "RUN")
        s.sync()


    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('PyWfs2Spatia4cacheINIT', message)

    def initGui(self):

        global __revision__
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.dirname(__file__)+'/iconSTART.png'
        self.iface.messageBar().pushMessage("Wfs2Spatia4cache initializing provider V"+__revision__, "START INIT..", level=Qgis.Info, duration=2)
        try:
          r = QgsProviderRegistry.instance()
          metadata = QgsProviderMetadata(PyWfs2Spatia4cacheProvider.providerKey(), PyWfs2Spatia4cacheProvider.description(), PyWfs2Spatia4cacheProvider.createProvider)
          r.registerProvider(metadata)
          r.providerMetadata(PyWfs2Spatia4cacheProvider.providerKey()) == metadata
          """prog = QProgressDialog('Working...', 'Cancel', 0, 100)
          #prog.setWindowModality(Qt.WindowModal)
          for i in range (1, 101):
              time.sleep(0.05)
          prog.setValue(i)
          if prog.wasCanceled():
            return
          """
          icon_path = os.path.dirname(__file__)+'/iconON.png'
        except:
          icon_path = os.path.dirname(__file__)+'/iconOFF.png'
          pass

        # Create action that will start plugin configuration
        self.action = QAction(
           QIcon(os.path.dirname(__file__)+"/icon.png"),
            u"&Convert...", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu(u"&Fournisseur WFS/Cache Spatia.", self.action)


        # Add cadastrehisto toolbar

        self.iface.messageBar().pushMessage("Wfs2Spatia4cache initializing provider  V"+__revision__, "END INIT .."+str(""), level=Qgis.Warning, duration=5)
        s = QgsSettings()
        if str(s.value("Wfs2Spatia4cache/mode", "XXX"))=="XXX":
           s.setValue("Wfs2Spatia4cache/mode", "AUTO")
        if str(s.value("Wfs2Spatia4cache/debug", "XXX"))=="XXX":
           s.setValue("Wfs2Spatia4cache/debug", "99999")
        s.setValue("Wfs2Spatia4cache/forceloading", "INIT")
        s.setValue("Wfs2Spatia4cache/loading", "INIT")
        s.setValue("Wfs2Spatia4cache/network.off", "NOT_USED")
        s.setValue("Wfs2Spatia4cache/automodewait", str( 60 * 60 * 8)  ) # 8 heures
        s.sync()
        # INIT in AUTO SWITCH
        self.changemode(True)
        """ 
        self.action2 = QAction( QIcon(os.path.dirname(__file__)+"/iconAUTO.png"),    u'Mode de Synchro', self.iface.mainWindow())
        self.action2.triggered.connect(self.changemode)
        self.toolbar = self.iface.addToolBar('&WFS avec cache local')
        self.toolbar.addAction(self.action2)
        self.toolbar.setObjectName("Wfs2Spatia4cache")			
        """ 

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        icon_path = os.path.dirname(__file__)+'/iconOFF.png'
        self.iface.removePluginMenu(u"&Fournisseur WFS/Cache Spatia.", self.action)

        self.iface.removeToolBarIcon(self.action2)

    def changemode(self, init=False):
        s = QgsSettings()
        CurrentMode=str(s.value("Wfs2Spatia4cache/mode", "XXX"))
        if not init:
           self.iface.removeToolBarIcon(self.action2)
           self.action2 = None
           self.toolbar = None

           if CurrentMode=="AUTO":
                  CurrentMode="OFF"
           else:
              if CurrentMode=="ON":
                  CurrentMode="AUTO"
              else:
                  if CurrentMode=="OFF":
                      CurrentMode="ON"
                  else:
                      CurrentMode="AUTO"

        s.setValue("Wfs2Spatia4cache/mode", CurrentMode)
        self.action2 = QAction( QIcon(os.path.dirname(__file__)+"/icon"+str(CurrentMode)+".png"),    u'Mode de Synchro', self.iface.mainWindow())
        self.action2.triggered.connect(self.changemode)
        self.toolbar = self.iface.addToolBar('&WFS avec cache local')
        self.toolbar.addAction(self.action2)
        self.toolbar.setObjectName("Wfs2Spatia4cache")			

        return


    def run(self):
        """Run method that performs all the real work"""
        #QgsMessageLog.logMessage("Message (Start) clearSession" , 'WFS2SQL4PLUGINIT (LOAD)',level=Qgis.MessageLevel(1) )

        self.iface.messageBar().pushMessage("Wfs2Spatia4cache provider converting...", "CONVERT..", level=Qgis.Critical, duration=1)
        layerList = QgsProject.instance().layerTreeRoot().findLayers()
        for layerTree in layerList:
              if layerTree.layer().providerType()=="WFS":

                 win32api.MessageBox(0, str(layerTree.layer().dataProvider().uri().uri()), 'QGISXXX', 0x00001000) 
                 QgsMessageLog.logMessage("convert:"+layerTree.name()+":"+str(layerTree.layer().dataProvider().uri().uri()) , 'WFS2SQL4CACHE (provider plugin menu) ',level=Qgis.MessageLevel(5) )
                 s = QgsSettings()
                 s.setValue("Wfs2Spatia4cache/forceloading", "RUN")
                 s.sync()
                 tmplayer = QgsVectorLayer( str(layerTree.layer().dataProvider().uri().uri())   ,    layerTree.name()+"(WFS2SQL)"    , 'WFS2SQL4C')
                 #QgsProject.instance().layerTreeRoot().insertChildNode(0, tmplayer)
                 s.setValue("Wfs2Spatia4cache/forceloading", "STOP")
                 s.sync()
                 QgsProject.instance().addMapLayer(tmplayer)
                 #node_layer2 = QgsLayerTreeLayer(tmplayer)
                 #QgsProject.instance().layerTreeRoot().insertChildNode(0, node_layer2)

              #5print(layer.name())
        pass