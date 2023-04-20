import os
import subprocess
import random
import sys
from PlotUtility import *

from ffmpeg_quality_metrics import FfmpegQualityMetrics

ffmpeg = "C:\\Users\\mradt\\Documents\\PathPrograms\\ffmpeg\\bin\\ffmpeg.exe"

bitrateResolutions ={}
bitrateResolutions["720p"] = [512, 1024, 2048, 3072, 4096]
bitrateResolutions["360p"] = [96, 128, 256, 384, 512,1024, 2048]
bitrateResolutions["180p"] = [64, 96, 128, 256, 384, 512,1024]

inputFiles = {}
inputFiles["720p"] = "dancing_org.1280x548.yuv"
inputFiles["360p"] = "dancing.640x274.yuv"
inputFiles["180p"] = "dancing.320x138.yuv"

inputFileSize = {}
inputFileSize["720p"] = "1280x548"
inputFileSize["360p"] = "640x274"
inputFileSize["180p"] = "320x138"



upsampleSizes = {}
upsampleSizes["360p"] = "1280x548"
upsampleSizes["180p"] = "1280x548"


upsampleResolutions = {}
upsampleResolutions["360p"] = "720p"
upsampleResolutions["180p"] = "720p"

PSNRToken = "PSNR Mean Y:"

outputDir = os.path.join(".", "Outputs")

# ffmpeg -s 640x274 -pix_fmt yuv420p -i dancing.640x274.yuv -b:v 96k -vcodec libx264 -pix_fmt yuv420p output.mp4
# ffmpeg -i .\CBRencoded\test96k.mp4 -vf scale=1280:548 .\Upscaled\output_test.mp4
# ffmpeg -i .\Upscaled\output_test.mp4 -c:v rawvideo -pix_fmt yuv420p .\Upscaled\output_test.yuv
# ffplay -f rawvideo -pixel_format yuv420p -video_size 1280x548 -i .\Upscaled\output_test.yuv



# Losslessly convert an mp4 to yuv
def MP4ToYUV(mp4Path):
    yuvPath = os.path.splitext(mp4Path)[0]+'.yuv' 
    
    if os.path.exists(yuvPath):
        os.remove(yuvPath)

    commandOutputFile = yuvPath + ".txt"
    if os.path.exists(commandOutputFile):
        os.remove(commandOutputFile)

    cmd = ffmpeg + " -i " + mp4Path + " -c:v rawvideo -pix_fmt yuv420p " + yuvPath+ " > " + commandOutputFile + " 2>&1"
    print(cmd)
    output = os.popen(cmd).read()
    return yuvPath

def YUVToMP4(yuvPath, size, mp4Path = None, forceDelete = True):
    # ffmpeg -s 640x274 -i dancing.640x274.yuv -c:v libx264 -s:v 640x274  mp4360p.mp4
    if mp4Path == None:
        mp4Path = os.path.splitext(yuvPath)[0]+'.mp4'
    if forceDelete and os.path.exists(mp4Path):
        os.remove(mp4Path)
    
    commandOutputFile = mp4Path + ".txt"
    if os.path.exists(commandOutputFile):
        os.remove(commandOutputFile)

    cmd = ffmpeg + " -s " + size + " -i " + yuvPath + " -c:v libx264 " + mp4Path + " > " + commandOutputFile + " 2>&1"
    print(cmd)
    output = os.popen(cmd).read()
    return mp4Path

# Converts a yuv to mp4 with the specified bitrate
def YUVToMP4Compress(yuvPath, size, bitrate, mp4Path = None, forceDelete = True):
    # ffmpeg -s 640x274 -i dancing.640x274.yuv -c:v libx264 -s:v 640x274  mp4360p.mp4
    if mp4Path == None:
        mp4Path = os.path.splitext(yuvPath)[0]+'.mp4'
    if forceDelete and os.path.exists(mp4Path):
        os.remove(mp4Path)
    
    commandOutputFile = mp4Path + ".txt"
    if os.path.exists(commandOutputFile):
        os.remove(commandOutputFile)

    # ffmpeg -s 640x274 -pix_fmt yuv420p -i dancing.640x274.yuv -b:v 96k -vcodec libx264 -pix_fmt yuv420p test96k.mp4
    cmd = ffmpeg + " -s " + size + " -pix_fmt yuv420p -i " + yuvPath + " -b:v " + str(bitrate) + "k -vcodec libx264 -pix_fmt yuv420p " + mp4Path + " > " + commandOutputFile + " 2>&1"
    print(cmd)
    output = os.popen(cmd).read()
    return mp4Path

# Takes a file and upsamples
def Upsample(source, outputPath, targetSize = "1280:548"):
    
    commandOutputFile = outputPath + ".txt"
    if os.path.exists(commandOutputFile):
        os.remove(commandOutputFile)
    
    if os.path.exists(outputPath):
        os.remove(outputPath)

    # ffmpeg -i input.mp4 -vf scale=1920x1080:flags=lanczos ouput_1080p.mp4
    cmd = ffmpeg + " -i " + source + " -vf scale=" +targetSize +" " + outputPath + " > " + commandOutputFile + " 2>&1"
    print(cmd)
    output = os.popen(cmd).read()

    return outputPath

# Take a yuv file, convert to mp4 at a specified bitrate, upsample, then convert back to yuv
def AdaptiveBitrateFlow(yuvFile, bitrate, originalSize):
    mp4Compressed = YUVToMP4Compress(yuvFile,originalSize, bitrate)
    mp4CompressedUpsampled = Upsample(mp4Compressed, os.path.splitext(mp4Compressed)[0] +"CompressedUpsampled.mp4")
    transformedYUV = MP4ToYUV(mp4CompressedUpsampled)
    return transformedYUV, mp4CompressedUpsampled, mp4Compressed

def CompareFilesPSNR(inputVideo, referenceVideo):
    psnr = -1
    print("Comparing", inputVideo, referenceVideo)
    ffqm = FfmpegQualityMetrics(referenceVideo,inputVideo)
    metrics = ffqm.calculate(['psnr'])
    psnr =  ffqm.get_global_stats()["psnr"]["psnr_avg"]["average"]

    return psnr

def GetPSNRFromFile(file):
    
    # Get out output and search for the psnr
    #  PSNR we want will be the last instance
    PSNRLine = ""
    f = open(file, "r")
    for line in f:
        if PSNRToken in line:
            PSNRLine = line
    f.close()

    # find the index of the psnr and extract the value from the output
    startIdx = PSNRLine.index(PSNRToken) + len(PSNRToken)
    endIdx = PSNRLine.index(" U:")
    psnr = float(PSNRLine[startIdx:endIdx])
    return psnr

def GenerateRDCurves():
    outputs = {}
    # The token will be use to find our PSNR from the ffmpeg command
    # Example
    # ffmpeg -s 640x274 -pix_fmt yuv420p -i dancing.640x274.yuv -b:v 96k -vcodec libx264 -pix_fmt yuv420p test96k.mp4
    # ffmpeg -i .\dancing_org.mp4 -b:v 2048k -vcodec: libx264 -psnr out_2048k.mp4
    for res in bitrateResolutions:
        outputs[res] = []
        for bitrate in bitrateResolutions[res]:
            print("Processing", res, bitrate, "kpbs", os.getcwd())
            outputFileName = res + "_" + str(bitrate) + "_kbps.mp4"
            outputPath = os.path.join(outputDir, outputFileName)

            if os.path.exists(outputPath):
                os.remove(outputPath)
            # ffmpeg -s 640x274 -pix_fmt yuv420p -i dancing.640x274.yuv -b:v 96k -vcodec libx264 -pix_fmt yuv420p test96k.mp4
            commandOutputFile = outputFileName + ".txt"
            command = ffmpeg + " -s " + inputFileSize[res] + " -i " + inputFiles[res] + " -pix_fmt yuv420p -b:v " + str(bitrate) + "k -vcodec: libx264 -psnr  " + outputPath + " > " + commandOutputFile + " 2>&1"
            print(command)
            output = os.popen(command).read()
            
            psnr = GetPSNRFromFile(commandOutputFile)
            print(psnr)

            outputs[res].append(psnr)

            # Cleanup
            if os.path.exists(outputPath):
                os.remove(outputPath)
            if os.path.exists(commandOutputFile):
                os.remove(commandOutputFile)

    Data = []
    for resolution in outputs:
        x = bitrateResolutions[resolution]
        y = outputs[resolution]
        color = None
        label = resolution
        alpha = 1.0
        Data.append(PlotData(x,y,color,label,alpha))
    
    title = "RD Curve, fixed bitrate compression"
    xLabel ="Bitrate (kbps)"
    yLabel = "PSNR Y (dB)"

    PlotHelper(title, xLabel, yLabel, scatterData = None, plotData = Data, histogramData = None)
    return Data
#       720p 1280 × 548 512 1024 2048 3072
#       360p 640 × 274 96 128 256 384 512 1024 2048
#       180p 320 × 138 64 96 128 256 512 1024


def CreateUpsampledMP4Files():
    # Create our 3 representation of the oringinal 720p file
    results = []
    filePaths = []
    # Upsample 360p to 720p and perform our RD curves. Example Command:
    # ffmpeg -i input.mp4 -vf scale=1920x1080:flags=lanczos ouput_1080p.mp4
    # Need to convert from yuv to mp4, then perform upsampling
    
    for sourceResolution in upsampleSizes:
        inputSize = inputFileSize[sourceResolution]
        targetSizes = upsampleSizes[sourceResolution]
        inputFile = inputFiles[sourceResolution]
        targetResolution = upsampleResolutions[sourceResolution]

        outputFileRoot = sourceResolution + "_To_"+ targetResolution
        outputFileName = os.path.join(outputDir, outputFileRoot + ".mp4" )

        mp4FilePath = YUVToMP4(inputFile, inputSize, outputFileName)
        print("Mp4 at " + mp4FilePath)
        filePaths.append(mp4FilePath)

        r = {}
        r["Source"] = sourceResolution
        r["TargetSize"] = targetSizes
        r["File"] = mp4FilePath
        r["Resolution"] = targetResolution

        results.append(r)

    return results

def GeneratePSNRComparison(inputVideo, referenceVideo, rates, resolution):
    PSNRs = []
    for bitrate in rates:
        print("Processing", inputVideo, bitrate, "kpbs", os.getcwd())
        outputFileName = "Upsampled_" + resolution + "_" + str(bitrate) + "_kbps.mp4"
        outputPath = os.path.join(outputDir, outputFileName)    
        if os.path.exists(outputPath):
            os.remove(outputPath)

        commandOutputFile = outputFileName + ".txt"
        # ffmpeg -i input_video.mp4 -i reference_video.mp4 -filter_complex "psnr" -f null /dev/null
        command = ffmpeg + " -i " + inputVideo + " -i " + referenceVideo + " -filter_complex \"psnr\" -f null NUL > " + commandOutputFile + " 2>&1"
        print(command)
        output = os.popen(command).read()

        psnr = GetPSNRFromFile(commandOutputFile)
        print(psnr)
        PSNRs.append(psnr)
        
            # Cleanup
        if os.path.exists(outputPath):
            os.remove(outputPath)
        if os.path.exists(commandOutputFile):
            os.remove(commandOutputFile)

    return PSNRs

def GeneratePSNRValuesForFileAndRates(file, rates, resolution):
    PSNRs = []
    for bitrate in rates:
        print("Processing", file, bitrate, "kpbs", os.getcwd())
        outputFileName = "Upsampled_" + resolution + "_" + str(bitrate) + "_kbps.mp4"
        outputPath = os.path.join(outputDir, outputFileName)    
        if os.path.exists(outputPath):
            os.remove(outputPath)

        commandOutputFile = outputFileName + ".txt"
        command = ffmpeg + " -i " + file + " -b:v " + str(bitrate) + "k -vcodec: libx264 -psnr " + outputPath + " > " + commandOutputFile + " 2>&1"
        print(command)
        output = os.popen(command).read()

        psnr = GetPSNRFromFile(commandOutputFile)
        print(psnr)
        PSNRs.append(psnr)
        
            # Cleanup
        if os.path.exists(outputPath):
            os.remove(outputPath)
        # if os.path.exists(commandOutputFile):
            # os.remove(commandOutputFile)

    return PSNRs

def GetDataPointsForUpsampledFiles():
    Datas = []
    Upsamples = CreateUpsampledMP4Files()
    for upsample in Upsamples:
        resolution = upsample["Resolution"]
        size = upsample["TargetSize"]
        bitrates = bitrateResolutions[resolution]
        file = upsample["File"]
        print("Generating PSNRs for ", file, "with bitrates", bitrates)
        referenceFileYUV = inputFiles[resolution]
        referenceFile = YUVToMP4(referenceFileYUV, size)
        PSNRs = GeneratePSNRValuesForFileAndRates(file, bitrates, resolution)
        # PSNRs = GeneratePSNRComparison(file, referenceFile, bitrates, resolution)

        if os.path.exists(referenceFile):
            os.remove(referenceFile)

        print(PSNRs)
        x = bitrates
        y = PSNRs
        color = None
        label = upsample["Source"] + " upsampled to " + resolution
        alpha = 1.0
        Datas.append(PlotData(x,y,color,label,alpha))
    return Datas
    

def main():
    # Generate refernce 720p to compare to all videos
    mp4Reference = YUVToMP4(inputFiles["720p"], inputFileSize["720p"])
    print("Reference 720p video created at", mp4Reference)
    
    resolution = "360p"
    yuvFile = inputFiles[resolution]
    bitrate = bitrateResolutions[resolution][0]
    originalSize = inputFileSize[resolution]
    transformedYUV, mp4CompressedUpsampled, mp4Compressed = AdaptiveBitrateFlow(yuvFile,bitrate,originalSize)

    psnr = CompareFilesPSNR(mp4CompressedUpsampled ,mp4Reference)
    print("PSNR:", psnr)
    return
    # GenerateRDCurves()
    Data = GetDataPointsForUpsampledFiles()
    title = "RD Curve, fixed bitrate compression for Upsampled files"
    xLabel ="Bitrate (kbps)"
    yLabel = "PSNR Y (dB)"

    PlotHelper(title, xLabel, yLabel, scatterData = None, plotData = Data, histogramData = None)

if __name__ == "__main__":
    main()