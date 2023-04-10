import os
import subprocess
import random
import sys
from PlotUtility import *

ffmpeg = "C:\\Users\\mradt\\Documents\\PathPrograms\\ffmpeg\\bin\\ffmpeg.exe"

resolutions ={}
resolutions["720p"] = [512, 1024, 2048, 3072]
resolutions["360p"] = [96, 128, 256, 384, 512,1024, 2048]
resolutions["180p"] = [64, 96, 128, 256, 384, 512,1024]

inputFiles = {}
inputFiles["720p"] = "dancing_org.1280x548.yuv"
inputFiles["360p"] = "dancing.640x274.yuv"
inputFiles["180p"] = "dancing.320x138.yuv"

inputFileSize = {}
inputFileSize["720p"] = "1280x548"
inputFileSize["360p"] = "640x274"
inputFileSize["180p"] = "320x138"

PSNRToken = "PSNR Mean Y:"

def MP4ToYUV(mp4Path):
    yuvPath = os.path.splitext(mp4Path)[0]+'.yuv' 
    cmd = ffmpeg + " -i " + mp4Path + " -c:v rawvideo -pix_fmt yuv420p " + yuvPath
    print(cmd)
    output = os.popen(cmd).read()
    return yuvPath

def GenerateRDCurves():
    outputDir = os.path.join(".", "Outputs")
    outputs = {}
    # The token will be use to find our PSNR from the ffmpeg command
    # Example
    # ffmpeg -s 640x274 -pix_fmt yuv420p -i dancing.640x274.yuv -b:v 96k -vcodec libx264 -pix_fmt yuv420p test96k.mp4
    # ffmpeg -i .\dancing_org.mp4 -b:v 2048k -vcodec: libx264 -psnr out_2048k.mp4
    for res in resolutions:
        outputs[res] = []
        for bitrate in resolutions[res]:
            print("Processing", res, bitrate, "kpbs", os.getcwd())
            outputFileName = res + "_" + str(bitrate) + "_kbps.mp4"
            outputPath = os.path.join(outputDir, outputFileName)

            if os.path.exists(outputPath):
                os.remove(outputPath)
            
            commandOutputFile = outputFileName + ".txt"
            command = ffmpeg + " -s " + inputFileSize[res] + " -i " + inputFiles[res] + " -pix_fmt yuv420p -b:v " + str(bitrate) + "k -vcodec: libx264 -psnr  -pix_fmt yuv420p " + outputPath + " > " + commandOutputFile + " 2>&1"
            print(command)
            output = os.popen(command).read()

            # Get out output and search for the psnr
            #  PSNR we want will be the last instance
            PSNRLine = ""
            f = open(commandOutputFile, "r")
            for line in f:
                if PSNRToken in line:
                    PSNRLine = line
            f.close()

            # find the index of the psnr and extract the value from the output
            startIdx = PSNRLine.index(PSNRToken) + len(PSNRToken)
            endIdx = PSNRLine.index(" U:")
            psnr = float(PSNRLine[startIdx:endIdx])
            print(psnr)

            outputs[res].append(psnr)

            # Cleanup
            if os.path.exists(outputPath):
                os.remove(outputPath)
            if os.path.exists(commandOutputFile):
                os.remove(commandOutputFile)

    Data = []
    for resolution in outputs:
        x = resolutions[resolution]
        y = outputs[resolution]
        color = None
        label = resolution
        alpha = 1.0
        Data.append(PlotData(x,y,color,label,alpha))
    
    title = "RD Curve, fixed bitrate compression"
    xLabel ="Bitrate (kbps)"
    yLabel = "PSNR Y (dB)"

    PlotHelper(title, xLabel, yLabel, scatterData = None, plotData = Data, histogramData = None)

#       720p 1280 × 548 512 1024 2048 3072
#       360p 640 × 274 96 128 256 384 512 1024 2048
#       180p 320 × 138 64 96 128 256 512 1024

        
def main():
    # sys.stdout = open('output.txt', 'w')
    GenerateRDCurves()
    # yuv = MP4ToYUV(inputFiles["720p"])
    # print(yuv)

if __name__ == "__main__":
    main()