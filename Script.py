######Ce script est utilisé comme structure de base pour créer des scripts d'automatisation sur ArcGIS Pro 
#Pensez à mettre un en-tête qui décrit l'utilité du script, fichiers en entrée et ce qu'il va produire comme données finales

###### Environment settings and library imports

print ('Env settings and lib import') #ajouter des prints permet à l'utilisateur de savoir où en est le processing lorsque le script tourne
import arcpy #import du module arcpy 
from arcpy import env #import de la fonction env du module arcpy
from arcpy.sa import * #import de toutes les fonctions d'arcpy.sa (extension Spatial Analyst)
from arcpy.ia import *
from tkinter import Tk
from tkinter.filedialog import askopenfilename


arcpy.env.overwriteOutput = True #autorise la réécriture d'un fichier si on veut enregistrer par dessus un autre fichier portant le même nom 
sr=arcpy.SpatialReference(2154)  ##cette ligne est à utiliser pour donner une référence, ici en exemple la référence sera RGF93 Lambert93; vous pouvez utiliser le code EPSG

from datetime import datetime #ces deux lignes permettent de stocker le temps de traitement du script
startTime = datetime.now() 

print ('Env settings and lib import: done')

print ('Script running')

######Data processing

try : ##c'est à cet endroit que l'on va faire tourner tous les outils

    
    ######Lien vers l'environnement de travail et création de la gdb######

##    ## Création de la gdb (ici facultatif car nous allons travailler hors GDB)
##    gdb_ask=input("Entrez le nom de votre gdb en sortie (pas d'espace ni de caractère spécial) et appuyez sur ENTREE : \n")
##    gdb_name = "{0}".format(gdb_ask) #récupère le nom renseigné par l'utilisateur dans la variable gdb_name
##    arcpy.CreateFileGDB_management(Input_folder, gdb_name) #cette fonction crée une géodatabase en prenant en argument le chemin d'accès à l'environnement de travail le nom de la gdb( (correspondant au nom entré par l'utilisateur dans la console)
    ##gdb_path = r'D:\_Emilien_Duclos\Projet_test\Test.gdb'
    ##output_path = r'D:\Emilien_Duclos\Projet_test\Output'
    ## Lien vers les input data
    inputgdb_ask = input("Rentrez le chemin d'acces de votre geodatabase \n")
    inputgdb_path = "{0}".format(inputgdb_ask)

    ## Lien vers le dossier output
    output_ask = input("Rentrez le chemin d'acces de votre dossier en sortie \n")
    output_path = "{0}".format(output_ask)
    arcpy.env.workspace = output_path #défini le dossier de sortie dans l'environnement de travail, dans lequel seront enregistrées par défaut les données en sortie

    print ('Environnements mis à jour')
    
    ####### A vous de jouer maintenant

    root = Tk()
    root.withdraw()
    filename = askopenfilename(title="Select file")

    #input_laz_file = askopenfilename(
    #title="Sélectionner un fichier .laz",
    #filetypes=[("Fichiers .laz", "*.laz")],)

    print("Début de la conversion")
    arcpy.conversion.ConvertLas(filename, output_path, "SAME_AS_INPUT", '', "NO_COMPRESSION", "REMOVE_VLR;REMOVE_EXTRA_BYTES", "Dalle.lasd", "ALL_FILES", 'PROJCS["RGF_1993_Lambert_93",GEOGCS["GCS_RGF_1993",DATUM["D_RGF_1993",SPHEROID["GRS_1980",6378137.0,298.257222101]],PRIMEM["Greenwich",0.0],UNIT["Degree",0.0174532925199433]],PROJECTION["Lambert_Conformal_Conic"],PARAMETER["False_Easting",700000.0],PARAMETER["False_Northing",6600000.0],PARAMETER["Central_Meridian",3.0],PARAMETER["Standard_Parallel_1",44.0],PARAMETER["Standard_Parallel_2",49.0],PARAMETER["Latitude_Of_Origin",46.5],UNIT["Meter",1.0]]')
    print("Fin de la conversion")

    print("Création du filtre MNT")
    arcpy.management.MakeLasDatasetLayer("Dalle.lasd", "Dalle_MNT_filter", "2", "2", "INCLUDE_UNFLAGGED", "INCLUDE_SYNTHETIC", "INCLUDE_KEYPOINT", "EXCLUDE_WITHHELD", None, "INCLUDE_OVERLAP")
    print("fin Création du filtre MNT")
    
    print("Création MNT")
    arcpy.conversion.LasDatasetToRaster("Dalle_MNT_filter", "MNT", "ELEVATION", "BINNING MINIMUM LINEAR", "FLOAT", "CELLSIZE", 1, 1)
    print("Fin Création MNT")

    print("Création filtre MNS")
    arcpy.management.MakeLasDatasetLayer("Dalle.lasd", "Dalle_MNS_filter", "1;6", "1", "INCLUDE_UNFLAGGED", "INCLUDE_SYNTHETIC", "INCLUDE_KEYPOINT", "EXCLUDE_WITHHELD", None, "INCLUDE_OVERLAP")
    print("Fin création filtre MNS")

    print("Création MNS")
    arcpy.conversion.LasDatasetToRaster("Dalle_MNS_filter", "MNS", "ELEVATION", "BINNING AVERAGE LINEAR", "FLOAT", "CELLSIZE", 1, 1)
    print("Fin Création MNS")

    print("Création BHM")
    out_raster = Minus("mns", "mnt"); out_raster.save("bhm")
    print("Fin Création BHM")

    print("Debut LAS Point Statistics")
    arcpy.management.LasPointStatsAsRaster("Dalle_MNS_filter", "Stats", "PREDOMINANT_CLASS", "CELLSIZE", "1")
    print("Fin LAS Point Statistics")

    print("Debut du CON")
    out_CON = Con("Stats", "1", "0", "VALUE = 6")
    out_CON.save("CON.tif")
    print("Fin du CON")

    print("Debut Raster to Polygon")
    arcpy.conversion.RasterToPolygon("CON.tif", "Con_pol.shp", "SIMPLIFY", "Value", "SINGLE_OUTER_PART", None)
    print("Fin Raster to Polygon")

    print("Debut Make Feature Layer")
    arcpy.management.MakeFeatureLayer("Con_pol.shp", "CON_lyr")
    print("Fin Make Feature Layer")

    print("Debut Select Layer by Attribute")
    select = arcpy.management.SelectLayerByAttribute("CON_lyr", "NEW_SELECTION", "gridcode = 1")
    print("Fin Select Layer by Attribute")

    print("Debut copy features")
    arcpy.management.CopyFeatures(select, "CON_true")
    print("Fin copy features")

    print("Debut RBF")
    arcpy.ddd.RegularizeBuildingFootprint("CON_true", "RBF", "ANY_ANGLE", "1", "1", "0,15", "2", 0.1, 1000000, None, "1 Meters")
    print("Fin RBF")
    
    #eliminate parts
    print("Debut Eliminate Polygon Part")
    arcpy.management.EliminatePolygonPart("RBF", "RBF_eliminated", "AREA", "99 SquareMeters", 0, "CONTAINED_ONLY")
    print("Fin Eliminate Polygon Part")

    print("Debut Clip Raster")
    arcpy.management.Clip("bhm", "", "bhm_CLIP.tif", "RBF_eliminated.shp", "-3,402823e+38", "ClippingGeometry", "MAINTAIN_EXTENT")
    print("Fin Clip Raster")

    #zonal statistics pour mettre la z dans le fichier polygone
    print("Debut Zonal Statistic")
    out_rasterZ = arcpy.ia.ZonalStatistics("RBF_eliminated.shp", "Id", "bhm_CLIP.tif", "MEAN"); out_rasterZ.save("Zonal.tif")
    print("Fin Zonal Statistic")

    #raster calculator RoundUp
    print("Debut Raster Calculator")
    out_rasterUP = RoundUp("Zonal.tif")
    out_rasterUP.save("Zonal_UP.tif")
    print("Fin Raster Calculator")

    #outil Int pour passer de valeur double a integer
    print("Debut Int")
    out_rasterINT = arcpy.ia.Int("Zonal_UP.tif"); out_rasterINT.save("Zonal_UP_INT.tif")
    print("Fin Int")

    print("Debut Raster to Polygon")
    arcpy.conversion.RasterToPolygon("Zonal_UP_INT.tif", "Zonal_UP_INT_POL.shp", "SIMPLIFY", "Value", "SINGLE_OUTER_PART", None)
    print("Fin Raster to Polygon")

    print("Debut Spatial Join")
    #arcpy.analysis.SpatialJoin("RBF_eliminated.shp", "Zonal_UP_INT_POL.shp", "Final_polygon.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", "INTERSECT", None, '')
    arcpy.analysis.SpatialJoin("RBF_eliminated", "Zonal_UP_INT_POL", "Final_polygon.shp", "JOIN_ONE_TO_ONE", "KEEP_ALL", 'Id "Id" true true false 10 Long 0 10,First,#,RBF_eliminated,Id,-1,-1;gridcode "gridcode" true true false 10 Long 0 10,First,#,RBF_eliminated,gridcode,-1,-1;ORIG_OID "ORIG_OID" true true false 10 Long 0 10,First,#,RBF_eliminated,ORIG_OID,-1,-1;STATUS "STATUS" true true false 10 Long 0 10,First,#,RBF_eliminated,STATUS,-1,-1;ORIG_FID "ORIG_FID" true true false 10 Long 0 10,First,#,RBF_eliminated,ORIG_FID,-1,-1;Id_1 "Id" true true false 10 Long 0 10,First,#,Zonal_UP_INT_POL,Id,-1,-1;gridcode_1 "gridcode" true true false 10 Long 0 10,First,#,Zonal_UP_INT_POL,gridcode,-1,-1', "INTERSECT", None, '')
    print("Fin Spatial Join")

    #Multipatch
    print("Debut Multipatch Building")
    arcpy.ddd.LasBuildingMultipatch("Dalle.lasd", "Final_polygon.shp", "MNT", "Multipatch_Building.shp", "BUILDING_CLASSIFIED_POINTS", "0.5 Meters")
    print("Fin Multipatch Building")

    #Trouver un moyen de mettre un symbologie sympa (rouge batiment z élevé et jaune z faible)

    print("C'est fini c'est bien")
    
    ######Temps d'exécution

    endTime = datetime.now()- startTime  #ces deux lignes permettent de calculer et d'imprimer le temps d'exécution du script
    print ('Completed in {0} minutes'.format(endTime.total_seconds()/60.0))

except OSError as err :
    arcpy.AddError(err)
    print (err)
